import subprocess
import sys
import time
import os
import signal
import webbrowser
import threading

# Configuration
os.environ["MQTT_BROKER"] = "localhost"
os.environ["MQTT_PORT"] = "1883"
os.environ["SERIAL_PORT"] = "COM3"
os.environ["BAUD_RATE"] = "38400"
# Prevent Visualizer from locking COM8 by giving it a dummy port for habitat
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
        try:
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    print("Done.")

def open_browser():
    """Open the dashboard in the default browser after a delay"""
    print("Waiting for services to initialize...")
    time.sleep(5)
    print("Opening Dashboard...")
    webbrowser.open("http://localhost:5000")

def main():
    print("🚀 Starting SmartAgri System")
    print("==========================")

    # 1. Processor
    start_process(f"{sys.executable} processor.py", "Fog Processor")
    time.sleep(2)

    # 2. Visualizer
    start_process(f"{sys.executable} visualizer.py", "Visualizer Dashboard")
    time.sleep(2)

    # 3. STM32 Bridge
    start_process(f"{sys.executable} stm32_mqtt_bridge.py", "STM32 Bridge")
    
    # 4. Open Browser (in background thread to not block main loop)
    threading.Thread(target=open_browser, daemon=True).start()
    
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
