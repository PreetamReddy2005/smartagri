from flask import Flask, render_template, make_response, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import paho.mqtt.client as mqtt
import json
import threading
import time
import logging
from datetime import datetime
from collections import deque
from typing import Optional
try:
    from ml_model import predictor
except:
    predictor = None

try:
    from disease_detector import predict_disease, get_detector_status
    DISEASE_DETECTOR_AVAILABLE = True
except:
    DISEASE_DETECTOR_AVAILABLE = False
    print("⚠️  Disease detector not available")

# Configuration
APP_TEMPLATE = 'dashboard_new.html'  # Using user's custom Apple-style Bento Box dashboard (NOW FIXED!)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fog-visualizer-secret'
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, async_mode='threading', ping_timeout=60, ping_interval=25)

import os
from werkzeug.utils import secure_filename

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("pyserial not available - mushroom monitoring will not work")

# Upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Created uploads directory: {UPLOAD_FOLDER}")

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_SENSOR = "smartagri/sensor_data"
TOPIC_ACTUATOR = "smartagri/actuator_command"
TOPIC_FOG_STATUS = "smartagri/fog_status"
MOISTURE_THRESHOLD = 30

# Habitat Monitoring Configuration
HABITAT_SERIAL_PORT = os.getenv("HABITAT_PORT", "COM8")
HABITAT_BAUD_RATE = int(os.getenv("HABITAT_BAUD", 38400))
habitat_serial = None
habitat_data = {"temperature": None, "humidity": None, "soil_moisture": None}

# Data storage for charts (keep last 50 readings)
sensor_history = deque(maxlen=50)
actuator_history = deque(maxlen=50)

# Current state - UPDATED with all sensors, ML predictions, and crop-specific data
current_state = {
    "moisture": None,
    "temperature": None,
    "ph": None,
    "rain": None,
    "water_level": None,
    "pump_status": "OFF",
    "last_update": None,
    "alert": False,
    "crop_type": "tomatoes",  # Default crop
    "optimal_ranges": {},  # Crop-specific optimal ranges
    "ml_predictions": {
        "irrigation_needed": False,
        "predicted_moisture": None,
        "multi_step_forecast": [],
        "water_consumption": None
    },
    "suggestions": {
        "alerts": [],
        "recommendations": [],
        "irrigation_advice": {},
        "maintenance_tips": [],
        "risk_assessment": {}
    }
}

# Simulation State
SIMULATION_MODE = False
SIMULATION_OVERRIDES = {}

# MQTT client
mqtt_client: Optional[mqtt.Client] = None
mqtt_connected = False
pump_timers = {}
pump_lock = threading.Lock()  # Added for thread safety

def to_number_safe(v):
    """Safely convert value to float."""
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        try:
            return float(str(v).strip())
        except (TypeError, ValueError):
            return None

def on_connect(client, userdata, flags, rc):
    """Callback when MQTT client connects."""
    global mqtt_connected
    if rc == 0:
        print("Visualizer connected to MQTT Broker!")
        mqtt_connected = True
        try:
            client.subscribe(TOPIC_SENSOR, qos=1)
            client.subscribe(TOPIC_ACTUATOR, qos=1)
            client.subscribe(TOPIC_FOG_STATUS, qos=1)
            print(f"Subscribed to {TOPIC_SENSOR}, {TOPIC_ACTUATOR}, {TOPIC_FOG_STATUS}")
        except Exception as e:
            print(f"Subscribe error: {e}")
    else:
        mqtt_connected = False
        print(f"Failed to connect, return code {rc}")
        # Retry connection after delay
        time.sleep(5)
        start_mqtt()

def on_disconnect(client, userdata, rc):
    """Callback when MQTT client disconnects."""
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        print(f"Unexpected disconnection (code {rc}). Reconnecting...")

def on_message(client, userdata, msg):
    """Callback when MQTT message is received."""
    global current_state, pump_timers
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if msg.topic == TOPIC_SENSOR:
            # Sensor data received - ALL SENSORS
            moisture = to_number_safe(data.get("moisture"))
            temperature = to_number_safe(data.get("temp", data.get("temperature")))
            ph = to_number_safe(data.get("ph"))
            rain = data.get("rain")
            water_level = to_number_safe(data.get("water_level"))
            
            # Update current state (Only update if value is present)
            if moisture is not None: current_state["moisture"] = moisture
            if temperature is not None: current_state["temperature"] = temperature
            if ph is not None: current_state["ph"] = ph
            if rain is not None: current_state["rain"] = rain
            if water_level is not None: current_state["water_level"] = water_level
            
            current_state["last_update"] = timestamp
            if moisture is not None:
                current_state["alert"] = moisture < MOISTURE_THRESHOLD
            
            # Add to history
            sensor_history.append({
                "time": timestamp,
                "moisture": moisture,
                "temperature": temperature,
                "ph": ph,
                "rain": rain,
                "water_level": water_level
            })
            
            print(f"[SENSOR] moisture={moisture}, temp={temperature}, ph={ph}, rain={rain}, water={water_level}")
            
            # Only emit real data if NOT in simulation mode
            if not SIMULATION_MODE:
                try:
                    socketio.emit('sensor_update', {
                        "moisture": moisture,
                        "temperature": temperature,
                        "ph": ph,
                        "rain": rain,
                        "water_level": water_level,
                        "timestamp": timestamp,
                        "alert": current_state["alert"]
                    })
                    
                    # BRIDGE TO HABITAT MONITOR
                    global habitat_data
                    habitat_data = {
                        "temperature": temperature,
                        "humidity": 65.0, # Default/Mock humidity since STM32 might not send it in this packet
                        "soil_moisture": moisture,
                        "port": "MQTT"
                    }
                    socketio.emit('habitat_update', habitat_data)
                    
                except Exception as e:
                    print(f"Error emitting sensor_update: {e}")
            
        elif msg.topic == TOPIC_ACTUATOR:
            # Actuator command received
            action = data.get("action", "").lower()
            duration = to_number_safe(data.get("duration")) or 5
            reason = data.get("reason", "")
            
            print(f"[ACTUATOR] action={action}, duration={duration}, reason={reason}")
            
            if "pump" in action and "on" in action:
                current_state["pump_status"] = "ON"
                actuator_history.append({
                    "time": timestamp,
                    "action": "ON",
                    "duration": duration
                })
                
                try:
                    socketio.emit('actuator_update', {
                        "status": "ON",
                        "action": "turn_on_pump",
                        "duration": duration,
                        "timestamp": timestamp
                    })
                except Exception as e:
                    print(f"Error emitting actuator_update (ON): {e}")
                
                # Cancel any existing timer (with thread safety)
                with pump_lock:
                    if "pump_off" in pump_timers:
                        timer = pump_timers.pop("pump_off")
                        if timer and timer.is_alive():
                            timer.cancel()
                
                # Turn off after duration
                def turn_off_after_delay():
                    try:
                        current_state["pump_status"] = "OFF"
                        actuator_history.append({
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "action": "OFF",
                            "reason": "duration_expired"
                        })
                        socketio.emit('actuator_update', {
                            "status": "OFF",
                            "action": "stop_pump",
                            "reason": "duration_expired",
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                    except Exception as e:
                        print(f"Error in turn_off_after_delay: {e}")
                
                timer = threading.Timer(duration, turn_off_after_delay)
                timer.daemon = True
                timer.start()
                
                with pump_lock:
                    pump_timers["pump_off"] = timer
                
            elif "pump" in action and "stop" in action:
                current_state["pump_status"] = "OFF"
                
                # Cancel any existing timer (with thread safety)
                with pump_lock:
                    if "pump_off" in pump_timers:
                        timer = pump_timers.pop("pump_off")
                        if timer and timer.is_alive():
                            timer.cancel()
                
                actuator_history.append({
                    "time": timestamp,
                    "action": "OFF",
                    "reason": reason or "manual_stop"
                })
                
                try:
                    socketio.emit('actuator_update', {
                        "status": "OFF",
                        "action": "stop_pump",
                        "reason": reason or "manual_stop",
                        "timestamp": timestamp
                    })
                except Exception as e:
                    print(f"Error emitting actuator_update (OFF): {e}")
                    
        elif msg.topic == TOPIC_FOG_STATUS:
            # Fog status info
            msg_type = data.get("type", "")
            print(f"[FOG_STATUS] type={msg_type}, data={data}")

            if msg_type == "crop_change":
                # Update crop type and optimal ranges
                current_state["crop_type"] = data.get("crop_type", "tomatoes")
                current_state["optimal_ranges"] = data.get("optimal_ranges", {})

                # Emit crop change to clients
                try:
                    socketio.emit('crop_change', {
                        "crop_type": current_state["crop_type"],
                        "optimal_ranges": current_state["optimal_ranges"],
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                except Exception as e:
                    print(f"Error emitting crop_change: {e}")

            elif msg_type == "ml_prediction":
                # Update ML predictions in current state
                current_state["ml_predictions"]["irrigation_needed"] = data.get("irrigation_needed", False)
                current_state["ml_predictions"]["predicted_moisture"] = data.get("predicted_moisture")
                current_state["ml_predictions"]["multi_step_forecast"] = data.get("multi_step_forecast", [])
                current_state["ml_predictions"]["water_consumption"] = data.get("water_consumption")

                # Emit ML predictions to clients
                try:
                    socketio.emit('ml_prediction_update', {
                        "irrigation_needed": current_state["ml_predictions"]["irrigation_needed"],
                        "predicted_moisture": current_state["ml_predictions"]["predicted_moisture"],
                        "multi_step_forecast": current_state["ml_predictions"]["multi_step_forecast"],
                        "water_consumption": current_state["ml_predictions"]["water_consumption"],
                        "crop_type": current_state["crop_type"],
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                except Exception as e:
                    print(f"Error emitting ml_prediction_update: {e}")

            elif msg_type == "crop_suggestions":
                # Update suggestions in current state
                suggestions_data = data.get("suggestions", {})
                current_state["suggestions"]["alerts"] = suggestions_data.get("alerts", [])
                current_state["suggestions"]["recommendations"] = suggestions_data.get("recommendations", [])
                current_state["suggestions"]["irrigation_advice"] = suggestions_data.get("irrigation_advice", {})
                current_state["suggestions"]["maintenance_tips"] = suggestions_data.get("maintenance_tips", [])
                current_state["suggestions"]["risk_assessment"] = suggestions_data.get("risk_assessment", {})

                # Emit suggestions to clients
                try:
                    socketio.emit('suggestions_update', {
                        "alerts": current_state["suggestions"]["alerts"],
                        "recommendations": current_state["suggestions"]["recommendations"],
                        "irrigation_advice": current_state["suggestions"]["irrigation_advice"],
                        "maintenance_tips": current_state["suggestions"]["maintenance_tips"],
                        "risk_assessment": current_state["suggestions"]["risk_assessment"],
                        "crop_type": current_state["crop_type"],
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                except Exception as e:
                    print(f"Error emitting suggestions_update: {e}")
            
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def start_mqtt():
    """Start MQTT client in a separate thread."""
    global mqtt_client
    try:
        # FIXED: Use CallbackAPIVersion for paho-mqtt 2.0+
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="fog_visualizer")
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message

        print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("MQTT client started")
    except Exception as e:
        print(f"MQTT connection error: {e}")
        # Retry after 5 seconds
        time.sleep(5)
        start_mqtt()

@app.route('/')
def index():
    """Main dashboard page."""
    try:
        response = make_response(render_template(APP_TEMPLATE))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"Error rendering dashboard: {e}")
        return {"error": str(e)}, 500

@app.route('/api/ai-insights')
def get_ai_insights():
    """Get AI model performance and insights."""
    try:
        if predictor:
            insights = predictor.get_ai_insights()
            return jsonify(insights)
        return jsonify({"error": "AI model not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/field_map')
def field_map():
    """Render the field map page."""
    return render_template('field_map.html')

@app.route('/habitat_monitor')
def habitat_monitor():
    """Render the habitat monitoring page."""
    return render_template('habitat_monitor.html')

# Digital Twin 3D - Disabled for now
# @app.route('/digital_twin_3d')
# def digital_twin_3d():
#     """Render the 3D Digital Twin visualization page."""
#     return render_template('digital_twin_3d.html')


@app.route('/api/save_field', methods=['POST'])
def save_field():
    """Save field boundary GeoJSON."""
    try:
        data = request.json
        with open('field_data.json', 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({"status": "success", "message": "Field saved successfully"})
    except Exception as e:
        print(f"Error saving field: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_field', methods=['GET'])
def get_field():
    """Get saved field boundary GeoJSON."""
    try:
        if os.path.exists('field_data.json'):
            with open('field_data.json', 'r') as f:
                data = json.load(f)
            return jsonify(data)
        return jsonify({"type": "FeatureCollection", "features": []})
    except Exception as e:
        print(f"Error loading field: {e}")
        return jsonify({"error": str(e)}), 500

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/analyze-leaf', methods=['POST'])
def analyze_leaf():
    """
    Analyze a leaf image for disease detection.
    Accepts image file upload and returns disease prediction.
    """
    try:
        # Check if disease detector is available
        if not DISEASE_DETECTOR_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "Disease detector module not available"
            }), 503
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No file uploaded"
            }), 400
        
        file = request.files['file']
        
        # Check if file has a filename
        if file.filename == '':
            return jsonify({
                "status": "error",
                "message": "No file selected"
            }), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                "status": "error",
                "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(filepath)
        print(f"📸 Saved uploaded image: {filepath}")
        
        try:
            # Perform disease detection
            result = predict_disease(filepath)
            
            # Add timestamp and status
            result["status"] = "success"
            result["timestamp"] = datetime.now().isoformat()
            result["filename"] = filename
            
            print(f"🔬 Disease Analysis: {result['prediction']} ({result['confidence']}%) [Mock: {result['mock']}]")
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Error during prediction: {e}")
            return jsonify({
                "status": "error",
                "message": f"Analysis failed: {str(e)}"
            }), 500
            
        finally:
            # Clean up uploaded file
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"🗑️  Cleaned up: {filepath}")
            except Exception as e:
                print(f"Warning: Could not delete temporary file: {e}")
    
    except Exception as e:
        print(f"Error in analyze_leaf endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/detector-status', methods=['GET'])
def detector_status():
    """Get disease detector status."""
    try:
        if not DISEASE_DETECTOR_AVAILABLE:
            return jsonify({
                "available": False,
                "message": "Disease detector module not loaded"
            })
        
        status = get_detector_status()
        status["available"] = True
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "available": False,
            "error": str(e)
        }), 500


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("Client connected to WebSocket")
    try:
        # Send current state and history to newly connected client
        socketio.emit('initial_data', {
            "current": current_state,
            "sensor_history": list(sensor_history),
            "actuator_history": list(actuator_history)
        })
        # Send simulation status
        socketio.emit('simulation_status', {
            "enabled": SIMULATION_MODE,
            "overrides": SIMULATION_OVERRIDES
        })
    except Exception as e:
        print(f"Error in handle_connect: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print("Client disconnected from WebSocket")

@socketio.on('toggle_simulation')
def handle_toggle_simulation(data):
    """Enable/Disable Ghost Mode (Digital Twin Simulation)."""
    global SIMULATION_MODE
    SIMULATION_MODE = bool(data.get('enabled', False))
    print(f"👻 Simulation Mode: {'ON' if SIMULATION_MODE else 'OFF'}")
    socketio.emit('simulation_status', {"enabled": SIMULATION_MODE})

@socketio.on('update_simulation')
def handle_update_simulation(data):
    """Update simulation overrides (e.g. user slider inputs)."""
    global SIMULATION_OVERRIDES
    SIMULATION_OVERRIDES.update(data)
    print(f"🎛️ Simulation Overrides: {SIMULATION_OVERRIDES}")

def run_simulation_loop():
    """Background thread for Digital Twin simulation."""
    print("Starting Digital Twin Simulation Loop...")
    while True:
        try:
            if SIMULATION_MODE and predictor:
                # Generate simulated data step
                sim_data = predictor.simulate_step(current_state, SIMULATION_OVERRIDES)
                
                # Create habitat update payload
                habitat_payload = {
                    "temperature": sim_data["temperature"],
                    "humidity": sim_data["humidity"],
                    "soil_moisture": sim_data["soil_moisture"],
                    "viability": sim_data["viability"],
                    "stress_factors": sim_data["stress_factors"],
                    "is_simulated": True,
                    "port": "DIGITAL TWIN"
                }
                
                # Emit to habitat monitor
                socketio.emit('habitat_update', habitat_payload)
                
                # Also emit to main dashboard (optional, but good for consistency)
                timestamp = datetime.now().strftime("%H:%M:%S")
                socketio.emit('sensor_update', {
                    "moisture": sim_data["soil_moisture"],
                    "temperature": sim_data["temperature"],
                    "ph": current_state.get("ph", 7.0), # Keep existing pH
                    "rain": 0,
                    "water_level": 50,
                    "timestamp": timestamp,
                    "alert": sim_data["soil_moisture"] < MOISTURE_THRESHOLD,
                    "is_simulated": True
                })
                
            time.sleep(1) # 1Hz simulation update
        except Exception as e:
            print(f"Simulation loop error: {e}")
            time.sleep(1)

def cleanup():
    """Cleanup before shutdown."""
    global mqtt_client, pump_timers
    
    print("Cleaning up...")
    
    # Cancel all timers
    with pump_lock:
        for key, timer in pump_timers.items():
            if timer and timer.is_alive():
                timer.cancel()
        pump_timers.clear()
    
    # Stop MQTT client
    if mqtt_client:
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        except Exception as e:
            print(f"Error stopping MQTT: {e}")

def start_habitat_monitor():
    """Start habitat serial monitoring in background."""
    global habitat_serial, habitat_data
    
    if not SERIAL_AVAILABLE:
        print("Habitat monitoring disabled - pyserial not installed")
        return
    
    try:
        print(f"Attempting to connect to habitat sensor on {HABITAT_SERIAL_PORT}...")
        habitat_serial = serial.Serial(
            HABITAT_SERIAL_PORT,
            HABITAT_BAUD_RATE,
            timeout=1
        )
        habitat_serial.reset_input_buffer()
        print(f"✅ Habitat monitoring started on {HABITAT_SERIAL_PORT}")
        
        # Read loop
        while True:
            try:
                if habitat_serial.in_waiting > 0:
                    line = habitat_serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        # Parse JSON: {"t":25.5,"h":60.2,"s":2500}
                        try:
                            data = json.loads(line)
                            temp = data.get('t')
                            humidity = data.get('h')
                            soil_raw = data.get('s')
                            
                            # Convert soil moisture (4095 is dry, 0 is wet)
                            soil_moisture = 100 - (int(soil_raw) * 100 / 4095) if soil_raw else None
                            
                            habitat_data = {
                                "temperature": temp,
                                "humidity": humidity,
                                "soil_moisture": soil_moisture,
                                "port": HABITAT_SERIAL_PORT
                            }
                            
                            # Broadcast to connected clients ONLY if not in simulation mode
                            if not SIMULATION_MODE:
                                socketio.emit('habitat_update', habitat_data)
                            
                        except json.JSONDecodeError:
                            pass  # Ignore malformed JSON
                            
                time.sleep(0.1)  # Small delay
                
            except Exception as e:
                print(f"Error reading habitat data: {e}")
                time.sleep(1)
                
    except serial.SerialException as e:
        print(f"❌ Could not connect to habitat sensor: {e}")
        print(f"   Make sure STM32 is connected to {HABITAT_SERIAL_PORT}")
    except Exception as e:
        print(f"Habitat monitoring error: {e}")

if __name__ == '__main__':
    # Start MQTT in background thread
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    
    # Start habitat monitoring in background thread
    habitat_thread = threading.Thread(target=start_habitat_monitor, daemon=True)
    habitat_thread.start()
    
    # Start simulation loop in background thread
    sim_thread = threading.Thread(target=run_simulation_loop, daemon=True)
    sim_thread.start()
    
    try:
        # Start Flask-SocketIO server
        print("Starting Fog Visualizer on http://0.0.0.0:5000")
        print("Dashboards available:")
        print("  - SmartAgri: http://localhost:5000")
        print("  - Habitat Monitor: http://localhost:5000/habitat_monitor")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if habitat_serial:
            try:
                habitat_serial.close()
            except:
                pass
        cleanup()