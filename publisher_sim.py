#!/usr/bin/env python3
# publisher_sim.py  -- publishes simulated sensor JSON periodically
import paho.mqtt.client as mqtt
import json, time, random, os
from datetime import datetime

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC = "smartagri/sensor_data"

# FIXED: Use CallbackAPIVersion for paho-mqtt 2.0+
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "publisher_sim")

def now_iso(): return datetime.utcnow().isoformat() + "Z"

def random_reading():
    # tweak ranges as needed
    return {
        "moisture": round(random.uniform(20, 55), 1),
        "temp": round(random.uniform(18, 34), 1),
        "ph": round(random.uniform(5.8, 7.6), 2),
        "rain": 1 if random.random() < 0.05 else 0,          # 5% chance rain
        "water_level": int(random.uniform(10, 100)),
        "timestamp": now_iso()
    }

def main():
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    try:
        while True:
            payload = random_reading()
            client.publish(TOPIC, json.dumps(payload), qos=1)
            print("Published:", payload)
            time.sleep(4)   # publish every 4s
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()