import serial
import time
import sys

PORT = "COM8"
BAUD = 38400

print(f"Opening {PORT} at {BAUD}...")
try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print("Open success. Listening for 10 seconds...")
    start = time.time()
    while time.time() - start < 10:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            print(f"Received: {data}")
        time.sleep(0.1)
    print("Done.")
    ser.close()
except Exception as e:
    print(f"Error: {e}")
