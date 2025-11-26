#!/usr/bin/env python3
"""
USB-TTL pH & Temperature Sensor Bridge
Reads sensor data from a dedicated USB-TTL converter and publishes to MQTT.
"""

import paho.mqtt.client as mqtt
import json
import time
import os
import serial
import serial.tools.list_ports
from datetime import datetime

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bridge_log.txt"),
        logging.StreamHandler()
    ]
)

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_SENSOR = "smartagri/sensor_data"
DEFAULT_BAUD_RATE = 9600  # Common for these sensors, can be overridden

class PhSensorBridge:
    def __init__(self):
        self.mqtt_client = None
        self.serial_port = None
        self.connected = False
        self.port_name = os.getenv("PH_SENSOR_PORT") # Optional: force a port

    def now_iso(self):
        return datetime.utcnow().isoformat() + "Z"

    def setup_mqtt(self):
        try:
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="ph_sensor_bridge")
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            logging.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            return True
        except Exception as e:
            logging.error(f"MQTT setup error: {e}")
            return False

    def detect_port(self):
        """Find the USB-TTL converter"""
        if self.port_name:
            logging.info(f"Using configured port: {self.port_name}")
            return self.port_name

        logging.info("Scanning for USB-TTL sensor...")
        ports = list(serial.tools.list_ports.comports())
        
        # Look for common USB-Serial chips (CH340, CP210x, FTDI)
        candidates = []
        for p in ports:
            desc = p.description.lower()
            if "usb" in desc or "serial" in desc or "uart" in desc:
                candidates.append(p)
        
        # Filter out the STM32 if possible (usually has STM in name)
        candidates = [p for p in candidates if "stm" not in p.description.lower()]

        if not candidates:
            logging.error("No likely USB-TTL ports found.")
            return None
        
        if len(candidates) == 1:
            logging.info(f"Found candidate: {candidates[0].device} ({candidates[0].description})")
            return candidates[0].device
        
        logging.warning("Multiple candidates found:")
        for i, p in enumerate(candidates):
            logging.info(f"  {i}: {p.device} - {p.description}")
        
        # Default to the first one that isn't COM1 (usually system)
        for p in candidates:
            if p.device != "COM1":
                logging.info(f"Defaulting to {p.device}")
                return p.device
                
        return candidates[0].device

    def parse_data(self, line):
        """
        Flexible parser for unknown data format.
        Tries: JSON -> Key:Value -> CSV -> Raw Number
        """
        line = line.strip()
        if not line:
            return None

        data = {}
        
        # 1. Try JSON
        try:
            data = json.loads(line)
            # Normalize keys
            return self.normalize_data(data)
        except json.JSONDecodeError:
            pass

        # 2. Try Key:Value (e.g., "ph:7.0, temp:25")
        if ":" in line:
            try:
                parts = line.replace(',', ' ').split()
                for part in parts:
                    if ":" in part:
                        k, v = part.split(':', 1)
                        data[k.lower()] = float(v)
                if data:
                    return self.normalize_data(data)
            except ValueError:
                pass

        # 3. Try CSV (assuming order: ph, temp OR temp, ph)
        # We need to guess which is which based on range
        if "," in line or " " in line:
            try:
                parts = line.replace(',', ' ').split()
                nums = [float(p) for p in parts if self.is_float(p)]
                
                if len(nums) >= 2:
                    # Heuristic: pH is usually 0-14, Temp is usually 10-40 (in agri context)
                    # But they overlap. Let's assume standard order if ambiguous.
                    # Common: pH, Temp
                    
                    val1, val2 = nums[0], nums[1]
                    
                    # If one is clearly pH (>14 is definitely not pH usually, but temp can be)
                    if val1 <= 14 and val2 > 14:
                        data['ph'] = val1
                        data['temp'] = val2
                    elif val1 > 14 and val2 <= 14:
                        data['temp'] = val1
                        data['ph'] = val2
                    else:
                        # Ambiguous, assume pH first
                        data['ph'] = val1
                        data['temp'] = val2
                        
                    return self.normalize_data(data)
            except ValueError:
                pass

        logging.warning(f"Could not parse line: {line}")
        return None

    def is_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def normalize_data(self, data):
        """Ensure keys match what the dashboard expects"""
        out = {}
        
        # pH
        if 'ph' in data: out['ph'] = float(data['ph'])
        elif 'p' in data: out['ph'] = float(data['p'])
        
        # Temp
        if 'temp' in data: out['temperature'] = float(data['temp'])
        elif 't' in data: out['temperature'] = float(data['t'])
        elif 'temperature' in data: out['temperature'] = float(data['temperature'])
        
        if out:
            out['timestamp'] = self.now_iso()
            return out
        return None

    def run(self):
        logging.info("Starting pH Sensor Bridge...")
        if not self.setup_mqtt():
            return

        port = self.detect_port()
        if not port:
            logging.error("No port found. Exiting.")
            return

        logging.info(f"Opening {port} at {DEFAULT_BAUD_RATE}...")
        
        try:
            with serial.Serial(port, DEFAULT_BAUD_RATE, timeout=1) as ser:
                logging.info("Serial connected. Waiting for data...")
                while True:
                    if ser.in_waiting:
                        try:
                            line = ser.readline().decode('utf-8', errors='ignore')
                            logging.info(f"Raw: {line.strip()}") # Debug log
                            
                            data = self.parse_data(line)
                            if data:
                                payload = json.dumps(data)
                                self.mqtt_client.publish(TOPIC_SENSOR, payload)
                                logging.info(f"Published: {data}")
                        except Exception as e:
                            logging.error(f"Error processing line: {e}")
                    
                    time.sleep(0.1)
        except Exception as e:
            logging.error(f"Serial error: {e}")
        finally:
            self.mqtt_client.loop_stop()

if __name__ == "__main__":
    bridge = PhSensorBridge()
    bridge.run()
