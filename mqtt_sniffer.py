import paho.mqtt.client as mqtt
import time
import os

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC = "smartagri/sensor_data"

messages = []

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker. Subscribing to {TOPIC}...")
        client.subscribe(TOPIC)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print(f"RECEIVED: {payload}")
        messages.append(payload)
    except Exception as e:
        print(f"Error decoding message: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Starting sniffer...")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    # Listen for 10 seconds
    start_time = time.time()
    while time.time() - start_time < 10:
        if messages:
            break
        time.sleep(0.1)
        
    client.loop_stop()
    client.disconnect()
    
    if not messages:
        print("No messages received in 10 seconds.")
    else:
        print(f"Captured {len(messages)} messages.")

except Exception as e:
    print(f"An error occurred: {e}")
