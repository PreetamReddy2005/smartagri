#!/usr/bin/env python3
"""
STM32 to MQTT Bridge
Reads JSON sensor data from STM32 via serial and publishes to MQTT broker
Compatible with the fog computing dashboard system
"""

import paho.mqtt.client as mqtt
import json
import time
import os
import serial
import sys
from datetime import datetime
from collections import deque

# Configuration
import serial.tools.list_ports

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_SENSOR = "smartagri/sensor_data"
TOPIC_CROP = "smartagri/crop_selection"

# Serial configuration
DEFAULT_BAUD_RATE = int(os.getenv("BAUD_RATE", 38400))

# Data validation and statistics
class SensorValidator:
    def __init__(self):
        self.history = {
            'moisture': deque(maxlen=10),
            'temp': deque(maxlen=10),
            'ph': deque(maxlen=10),
            'water_level': deque(maxlen=10)
        }
        self.error_count = 0
        self.valid_count = 0
    
    def validate_and_filter(self, data):
        """Validate sensor readings and apply basic filtering"""
        validated = {}
        
        # Moisture (0-100%)
        moisture = data.get('moisture')
        if moisture is not None and 0 <= moisture <= 100:
            self.history['moisture'].append(moisture)
            validated['moisture'] = round(moisture, 1)
        else:
            print(f"⚠️  Invalid moisture: {moisture}")
            validated['moisture'] = self._get_average('moisture')
        
        # Temperature (-40 to 80°C)
        temp = data.get('temp', data.get('temperature'))
        if temp is not None and -40 <= temp <= 80:
            self.history['temp'].append(temp)
            validated['temperature'] = round(temp, 1)
        else:
            print(f"⚠️  Invalid temperature: {temp}")
            validated['temperature'] = self._get_average('temp')
        
        # pH (0-14)
        ph = data.get('ph')
        if ph is not None and 0 <= ph <= 14:
            self.history['ph'].append(ph)
            validated['ph'] = round(ph, 2)
        else:
            print(f"⚠️  Invalid pH: {ph}")
            validated['ph'] = self._get_average('ph')
        
        # Rain (0 or 1)
        rain = data.get('rain')
        if rain is not None:
            validated['rain'] = 1 if rain else 0
        else:
            validated['rain'] = 0
        
        # Water level (0-100%)
        water_level = data.get('water_level')
        if water_level is not None and 0 <= water_level <= 100:
            self.history['water_level'].append(water_level)
            validated['water_level'] = int(water_level)
        else:
            print(f"⚠️  Invalid water level: {water_level}")
            validated['water_level'] = self._get_average('water_level')
        
        return validated
    
    def _get_average(self, key):
        """Get average of recent valid values"""
        if self.history[key]:
            avg = sum(self.history[key]) / len(self.history[key])
            return round(avg, 2 if key == 'ph' else 1)
        return None

class STM32Bridge:
    def __init__(self):
        self.mqtt_client = None
        self.serial_port = None
        self.validator = SensorValidator()
        self.connected = False
        self.current_crop = "tomatoes"
        
    def now_iso(self):
        return datetime.utcnow().isoformat() + "Z"
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback when MQTT connects"""
        if rc == 0:
            print("✅ Connected to MQTT broker")
            self.connected = True
            # Subscribe to crop selection topic
            client.subscribe(TOPIC_CROP, qos=1)
        else:
            print(f"❌ MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback when MQTT disconnects"""
        print(f"⚠️  Disconnected from MQTT broker (code {rc})")
        self.connected = False
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages (e.g., crop selection)"""
        try:
            if msg.topic == TOPIC_CROP:
                data = json.loads(msg.payload.decode())
                self.current_crop = data.get("crop_type", self.current_crop)
                print(f"🌱 Crop changed to: {self.current_crop}")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def setup_mqtt(self):
        """Initialize MQTT connection"""
        try:
            self.mqtt_client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION1, 
                client_id="stm32_bridge"
            )
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            print(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 1
            
            if not self.connected:
                raise Exception("MQTT connection timeout")
                
            return True
        except Exception as e:
            print(f"❌ MQTT setup error: {e}")
            return False
    
    def detect_port(self):
        """Auto-detect STM32 COM port"""
        print("🔍 Scanning for STM32 device...")
        ports = list(serial.tools.list_ports.comports())
        
        # 1. Check for STM32/STLink specific keywords
        for p in ports:
            desc = p.description.lower()
            # hwid = p.hwid.lower()
            if "stm" in desc or "stlink" in desc or "stmicro" in desc:
                print(f"✅ Found STM32 device: {p.device} ({p.description})")
                return p.device
                
        # 2. Fallback: Check for generic USB Serial if only one exists
        usb_ports = [p for p in ports if "usb" in p.description.lower()]
        if len(usb_ports) == 1:
            print(f"⚠️  Assuming USB Serial device: {usb_ports[0].device}")
            return usb_ports[0].device
            
        # 3. Last resort: Environment variable or default
        env_port = os.getenv("SERIAL_PORT")
        if env_port:
            print(f"⚠️  Using configured port: {env_port}")
            return env_port
            
        print("❌ No STM32 device found. Available ports:")
        for p in ports:
            print(f"  - {p.device}: {p.description}")
        return None

    def setup_serial(self):
        """Initialize serial connection"""
        port = self.detect_port()
        if not port:
            return False

        try:
            print(f"Opening serial port: {port} at {DEFAULT_BAUD_RATE} baud")
            self.serial_port = serial.Serial(
                port, 
                DEFAULT_BAUD_RATE, 
                timeout=2,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Flush any existing data
            self.serial_port.reset_input_buffer()
            
            print("✅ Serial connection established")
            return True
        except serial.SerialException as e:
            print(f"❌ Serial error: {e}")
            print("\nTroubleshooting:")
            print("  1. Check if STM32 is connected")
            print("  2. Verify port name (use Device Manager on Windows)")
            print("  3. Ensure no other program is using the port")
            return False
    
    def parse_serial_line(self, line):
        """Parse JSON data from STM32"""
        # Debug: print raw line
        # print(f"Raw: {line}")
        
        try:
            # Try to parse as JSON
            data = json.loads(line)
            
            # Map STM32's shorthand fields to expected format
            # STM32 format: {"t":25.5, "h":60.5, "r":4095, "s":2000, "p":2048}
            # Expected: {"temp", "moisture", "ph", "rain", "water_level"}
            mapped_data = {}
            
            # Temperature: "t" -> "temp"
            if 't' in data:
                mapped_data['temp'] = data['t']
            elif 'temp' in data:
                mapped_data['temp'] = data['temp']
            elif 'temperature' in data:
                mapped_data['temp'] = data['temperature']
            
            # Soil Moisture: "s" -> "moisture" (convert from ADC 0-4095 to %)
            # STM32 sends: 4095 = dry (0%), 0 = wet (100%)
            if 's' in data:
                soil_raw = data['s']
                mapped_data['moisture'] = 100 - (soil_raw * 100 / 4095)
            elif 'moisture' in data:
                mapped_data['moisture'] = data['moisture']
            
            # pH: "p" -> "ph" (convert from ADC 0-4095 to pH 0-14)
            if 'p' in data:
                ph_raw = data['p']
                mapped_data['ph'] = (ph_raw / 4095) * 14
            elif 'ph' in data:
                mapped_data['ph'] = data['ph']
            
            # Rain: "r" -> "rain" (convert from ADC to boolean-ish)
            # Higher ADC = no rain detected, lower = rain
            if 'r' in data:
                rain_raw = data['r']
                mapped_data['rain'] = 1 if rain_raw < 2000 else 0
            elif 'rain' in data:
                mapped_data['rain'] = data['rain']
            
            # Humidity (optional): "h" -> just pass through for logging
            # Water level: use a default or calculate from humidity as proxy
            if 'water_level' in data:
                mapped_data['water_level'] = data['water_level']
            elif 'h' in data:
                # Use humidity as a proxy for water level (for demo)
                mapped_data['water_level'] = int(data['h']) if data['h'] <= 100 else 50
            else:
                mapped_data['water_level'] = 75  # Default
            
            validated = self.validator.validate_and_filter(mapped_data)
            validated['timestamp'] = self.now_iso()
            validated['crop_type'] = self.current_crop
            self.validator.valid_count += 1
            return validated
            
        except json.JSONDecodeError:
            # Try pipe format with labeled fields
            if "|" in line:
                try:
                    parts = [p.strip() for p in line.split('|')]
                    data = {
                        "moisture": 0,
                        "temp": 25.0,
                        "ph": 7.0,
                        "rain": 0,
                        "water_level": 50
                    }
                    
                    for i, part in enumerate(parts):
                        if "Moisture" in part or "moisture" in part:
                            # Extract number
                            val = float(''.join(c for c in part if c.isdigit() or c == '.'))
                            if val > 100:
                                data['moisture'] = (val / 4095.0) * 100
                            else:
                                data['moisture'] = val
                        
                        # Handle unlabeled first part as moisture
                        elif i == 0:
                             try:
                                 val = float(part)
                                 if val > 100:
                                    data['moisture'] = (val / 4095.0) * 100
                                 else:
                                    data['moisture'] = val
                             except ValueError:
                                 pass # Not a number, ignore

                        elif "pH" in part:
                            val = float(part.split(':')[1].strip())
                            if val > 14:
                                data['ph'] = (val / 4095.0) * 14
                            else:
                                data['ph'] = val
                                
                        elif "Temp" in part:
                             val = float(''.join(c for c in part if c.isdigit() or c == '.'))
                             data['temp'] = val

                    validated = self.validator.validate_and_filter(data)
                    validated['timestamp'] = self.now_iso()
                    validated['crop_type'] = self.current_crop
                    self.validator.valid_count += 1
                    return validated
                except Exception as e:
                    print(f"⚠️ Pipe parse error: {e}")

            # Try CSV format as fallback
            try:
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    data = {
                        "moisture": float(parts[0]),
                        "temp": float(parts[1]),
                        "ph": float(parts[2]),
                        "rain": int(parts[3]),
                        "water_level": int(parts[4])
                    }
                    validated = self.validator.validate_and_filter(data)
                    validated['timestamp'] = self.now_iso()
                    validated['crop_type'] = self.current_crop
                    self.validator.valid_count += 1
                    return validated
            except (ValueError, IndexError) as e:
                self.validator.error_count += 1
                # print(f"❌ Parse error: {e}")
                return None
        except Exception as e:
            self.validator.error_count += 1
            print(f"❌ Validation error: {e}")
            return None
        
        return None
    
    def publish_data(self, data):
        """Publish validated sensor data to MQTT"""
        try:
            payload = json.dumps(data)
            result = self.mqtt_client.publish(TOPIC_SENSOR, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Published: M:{data.get('moisture')}% "
                      f"T:{data.get('temperature')}°C "
                      f"pH:{data.get('ph')} "
                      f"R:{data.get('rain')} "
                      f"W:{data.get('water_level')}%")
                return True
            else:
                print(f"⚠️  Publish failed with code {result.rc}")
                return False
        except Exception as e:
            print(f"❌ Publish error: {e}")
            return False
    
    def print_statistics(self):
        """Print connection statistics"""
        total = self.validator.valid_count + self.validator.error_count
        if total > 0:
            success_rate = (self.validator.valid_count / total) * 100
            print(f"\n📊 Statistics: {self.validator.valid_count} valid, "
                  f"{self.validator.error_count} errors "
                  f"({success_rate:.1f}% success rate)")
    
    def run(self):
        """Main bridge loop"""
        print("=" * 60)
        print("STM32 to MQTT Bridge - Smart Agriculture System")
        print("=" * 60)
        
        # Setup connections
        if not self.setup_mqtt():
            return False
        
        if not self.setup_serial():
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            return False
        
        print("\n🚀 Bridge running... Press Ctrl+C to stop\n")
        
        try:
            line_buffer = ""
            last_stats_time = time.time()
            
            while True:
                try:
                    # Read data from serial
                    if self.serial_port.in_waiting > 0:
                        # Read byte by byte to handle partial lines
                        byte = self.serial_port.read(1).decode('utf-8', errors='ignore')
                        
                        if byte == '\n' or byte == '\r':
                            if line_buffer.strip():
                                # Process complete line
                                data = self.parse_serial_line(line_buffer.strip())
                                
                                if data:
                                    self.publish_data(data)
                                
                                line_buffer = ""
                        else:
                            line_buffer += byte
                    
                    # Print statistics every 30 seconds
                    if time.time() - last_stats_time > 30:
                        self.print_statistics()
                        last_stats_time = time.time()
                    
                    # Small delay to prevent CPU spinning
                    time.sleep(0.01)
                    
                except UnicodeDecodeError:
                    # Ignore decode errors
                    line_buffer = ""
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping bridge...")
            self.print_statistics()
        except Exception as e:
            print(f"\n❌ Runtime error: {e}")
        finally:
            # Cleanup
            if self.serial_port:
                self.serial_port.close()
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            print("✅ Bridge stopped cleanly")

def main():
    bridge = STM32Bridge()
    bridge.run()

if __name__ == "__main__":
    main()
