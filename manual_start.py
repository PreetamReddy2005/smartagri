import subprocess
import sys
import time
import os
import signal

# Configuration
os.environ["MQTT_BROKER"] = "localhost"
os.environ["MQTT_PORT"] = "1883"
# SERIAL_PORT is now auto-detected - no need to set it manually
# If you want to force a specific port, uncomment and set:
# os.environ["SERIAL_PORT"] = "COM8"
os.environ["BAUD_RATE"] = "38400"
# Prevent Visualizer from locking the port by giving it a dummy port for habitat
os.environ["HABITAT_PORT"] = "COM99"

processes = []

def start_process(command, name):
    print(f"Starting {name}...")
    p = subprocess.Popen(command, shell=True)
    processes.append((p, name))
    return p

def cleanup():
    print("\nStopping all services...")
    for p, name in processes:
        print(f"Killing {name}...")
        p.terminate()
        # On Windows terminate might not be enough for shell=True
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)])
    print("Done.")

def main():
    print("🚀 Starting SmartAgri System (Manual Mode)")
    print("==========================================")

    # 1. Processor
    start_process(f"{sys.executable} processor.py", "Fog Processor")
    time.sleep(2)

    # 2. Visualizer
    start_process(f"{sys.executable} visualizer.py", "Visualizer Dashboard")
    time.sleep(2)

    # 3. STM32 Bridge
    start_process(f"{sys.executable} stm32_mqtt_bridge.py", "STM32 Bridge")
    
    print("\n✅ All services started.")
    print("Dashboard: http://localhost:5000")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            for p, name in processes:
                if p.poll() is not None:
                    print(f"⚠️ {name} exited unexpectedly with code {p.returncode}")
                    # Optional: restart logic
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
