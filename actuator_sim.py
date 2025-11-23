#!/usr/bin/env python3
# actuator_sim.py -- listens to actuator_command and acts (simulated)
import paho.mqtt.client as mqtt
import json, time, os
from datetime import datetime

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC = "smartagri/actuator_command"

# FIXED: Use CallbackAPIVersion for paho-mqtt 2.0+
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "actuator_sim")

def now(): return datetime.utcnow().isoformat() + "Z"

def on_connect(c, u, f, rc):
    print("Actuator connected:", rc)
    c.subscribe(TOPIC)

def on_message(c, u, msg):
    try:
        data = json.loads(msg.payload.decode())
    except Exception as e:
        print("Bad actuator payload:", e); return

    print(f"[{now()}] Received actuator command:", data)
    # Simulate action
    action = data.get("action")
    if action == "turn_on_pump":
        duration = int(data.get("duration", 5))
        print(f"Sim: pump ON for {duration}s")
        # pretend to run pump then publish ack
        time.sleep(min(1, duration))  # don't actually wait full duration in sim
        ack = {"status": "ON", "timestamp": now()}
        client.publish("smartagri/actuator_state", json.dumps(ack), qos=1)
    elif action == "stop_pump":
        print("Sim: pump STOP")
        ack = {"status": "OFF", "timestamp": now()}
        client.publish("smartagri/actuator_state", json.dumps(ack), qos=1)
    else:
        print("Unknown action")

def main():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()

