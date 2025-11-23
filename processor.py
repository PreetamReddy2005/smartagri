#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import os
from datetime import datetime
from typing import Any, Optional
from ml_model import predictor

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

TOPIC_SENSOR = "smartagri/sensor_data"
TOPIC_ACTUATOR = "smartagri/actuator_command"
TOPIC_FOG_STATUS = "smartagri/fog_status"

# thresholds (will be overridden by crop-specific values)
MOISTURE_THRESHOLD = 30
PH_LOW = 5.5
PH_HIGH = 8.0
MIN_WATER_LEVEL = 20
IRRIGATION_DURATION_SEC = 5

# Import crop suggestions for dynamic thresholds
from suggestions import crop_suggestions

client: Optional[mqtt.Client] = None

def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _parse_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        try:
            return float(str(v).strip())
        except Exception:
            return None

def _parse_bool(v: Any) -> Optional[bool]:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    try:
        return bool(int(s))
    except Exception:
        return None

def publish_fog_status(payload: dict):
    if not isinstance(payload, dict):
        return
    payload.setdefault("timestamp", now_iso())
    if client is None:
        print("publish_fog_status: MQTT client not initialized")
        return
    try:
        client.publish(TOPIC_FOG_STATUS, json.dumps(payload), qos=1)
    except Exception as e:
        print("Failed to publish fog status:", e)

def on_connect(c, userdata, flags, rc):
    print("Connected to MQTT broker with rc:", rc)
    try:
        c.subscribe(TOPIC_SENSOR, qos=1)
        print("Subscribed to", TOPIC_SENSOR)
        publish_fog_status({"type": "status", "state": "online"})
    except Exception as e:
        print("Subscribe error:", e)

def on_message(c, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
    except Exception as e:
        print("Invalid payload:", e)
        return

    # Check for crop type change
    crop_type = data.get("crop_type")
    if crop_type:
        if predictor.set_crop_type(crop_type):
            print(f"✅ Crop type changed to: {crop_type}")
            # Publish crop change to dashboard
            publish_fog_status({
                "type": "crop_change",
                "crop_type": crop_type,
                "optimal_ranges": crop_suggestions.get_crop_optimal_ranges(crop_type)
            })
        else:
            print(f"❌ Invalid crop type: {crop_type}")

    # Get current crop profile for dynamic thresholds
    current_crop_profile = crop_suggestions.get_crop_profile()
    if current_crop_profile:
        # Override thresholds with crop-specific values
        moisture_threshold = current_crop_profile["moisture_optimal"]["critical"]
        ph_low = current_crop_profile["ph_optimal"]["critical_low"]
        ph_high = current_crop_profile["ph_optimal"]["critical_high"]
    else:
        # Fallback to defaults
        moisture_threshold = MOISTURE_THRESHOLD
        ph_low = PH_LOW
        ph_high = PH_HIGH

    # normalize fields
    moisture = data.get("moisture")
    temperature = data.get("temp", data.get("temperature"))
    ph = data.get("ph")
    rain = data.get("rain")
    water_level = data.get("water_level")

    print(f"[{now_iso()}] Sensor (Crop: {predictor.get_current_crop()}):", {"moisture": moisture, "temp": temperature, "ph": ph, "rain": rain, "water_level": water_level})

    # publish sensor to fog status for dashboard/bridge
    publish_fog_status({
        "type": "sensor_reading",
        "moisture": moisture,
        "temperature": temperature,
        "ph": ph,
        "rain": rain,
        "water_level": water_level,
        "crop_type": predictor.get_current_crop(),
        "alert": False
    })

    # Decision logic:
    # 1) If raining -> don't irrigate
    rain_bool = _parse_bool(rain)
    if rain_bool is True:
        print("Rain detected -> no irrigation")
        publish_fog_status({"type": "info", "message": "rain_detected"})
        return

    # 2) Low water tank -> stop pump and alert
    wl = _parse_float(water_level)
    if wl is not None and wl < MIN_WATER_LEVEL:
        print(f"Low water level ({wl}%) -> blocking pump")
        cmd = {"action": "stop_pump", "reason": "low_water", "timestamp": now_iso()}
        try:
            client.publish(TOPIC_ACTUATOR, json.dumps(cmd), qos=1)
        except Exception as e:
            print("Failed to publish actuator command:", e)
        publish_fog_status({"type": "actuator", "action": "stop_pump", "reason": "low_water"})
        return

    # 3) Moisture control with ML prediction
    mval = _parse_float(moisture)
    if mval is not None:
        # Get ML predictions
        current_data = {
            'moisture': mval,
            'temperature': _parse_float(temperature),
            'ph': _parse_float(ph),
            'rain': rain_bool,
            'water_level': _parse_float(water_level)
        }

        irrigation_pred = predictor.predict_irrigation_needed(current_data)
        multi_step_forecast = predictor.predict_multi_step(current_data, steps=4)
        water_consumption = predictor.predict_water_consumption(IRRIGATION_DURATION_SEC)

        print(f"ML Prediction (Crop: {predictor.get_current_crop()}): Irrigation needed: {irrigation_pred['needed']}, Predicted moisture: {irrigation_pred['predicted_moisture']:.1f}%")
        print(f"Multi-step forecast: {[f'{m:.1f}%' for m in multi_step_forecast]}")
        print(f"Predicted water consumption: {water_consumption:.1f}L")

        # Generate crop-specific suggestions
        suggestions = crop_suggestions.generate_suggestions(current_data, {
            "irrigation_needed": irrigation_pred['needed'],
            "predicted_moisture": irrigation_pred['predicted_moisture'],
            "multi_step_forecast": multi_step_forecast,
            "water_consumption": water_consumption
        })

        # Publish predictions and suggestions to fog status
        publish_fog_status({
            "type": "ml_prediction",
            "irrigation_needed": bool(irrigation_pred['needed']),
            "predicted_moisture": irrigation_pred['predicted_moisture'],
            "multi_step_forecast": multi_step_forecast,
            "water_consumption": water_consumption,
            "crop_type": predictor.get_current_crop()
        })

        # Publish suggestions
        publish_fog_status({
            "type": "crop_suggestions",
            "suggestions": suggestions
        })

        # Decision: Use ML prediction or current moisture with crop-specific threshold
        should_irrigate = mval < moisture_threshold or irrigation_pred['needed']

        if should_irrigate:
            print(f"Soil moisture {mval}% below {moisture_threshold}% (crop: {predictor.get_current_crop()}) or ML predicts need -> turn on pump")
            cmd = {"action": "turn_on_pump", "duration": IRRIGATION_DURATION_SEC, "timestamp": now_iso()}
            try:
                client.publish(TOPIC_ACTUATOR, json.dumps(cmd), qos=1)
            except Exception as e:
                print("Failed to publish actuator command:", e)
            publish_fog_status({"type": "actuator", "action": "turn_on_pump", "duration": IRRIGATION_DURATION_SEC})
        else:
            print("Soil moisture OK")

    # 4) pH alert (crop-specific)
    p = _parse_float(ph)
    if p is not None and (p < ph_low or p > ph_high):
        try:
            crop_name = current_crop_profile.get("name", predictor.get_current_crop()) if current_crop_profile else predictor.get_current_crop()
            print(f"⚠ pH {p} out of range ({ph_low} - {ph_high}) for {crop_name}")
            publish_fog_status({"type": "alert", "sensor": "ph", "value": p, "crop_type": predictor.get_current_crop()})
        except Exception as e:
            print("Failed to handle pH alert:", e)

def main():
    global client
    # FIXED: Use CallbackAPIVersion for paho-mqtt 2.0+
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="fog_processor")
    try:
        client.will_set(TOPIC_FOG_STATUS, json.dumps({"type": "status", "state": "offline", "timestamp": now_iso()}), qos=1)
    except Exception:
        pass

    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting to broker", MQTT_BROKER, MQTT_PORT)
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print("Unable to connect to MQTT broker:", e)
        return

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Stopping")
    finally:
        try:
            publish_fog_status({"type": "status", "state": "offline"})
        except Exception:
            pass
        try:
            client.disconnect()
        except Exception:
            pass

if __name__ == "__main__":
    main()