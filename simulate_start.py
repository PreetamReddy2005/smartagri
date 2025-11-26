import subprocess
import sys
import time
import os
import signal

# Configuration
os.environ["MQTT_BROKER"] = "localhost"
os.environ["MQTT_PORT"] = "1883"

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
    print("🚀 Starting SmartAgri System (SIMULATION MODE)")
    print("============================================")

    # 1. Processor
    start_process(f"{sys.executable} processor.py", "Fog Processor")
    time.sleep(2)

    # 2. Visualizer
    start_process(f"{sys.executable} visualizer.py", "Visualizer Dashboard")
    time.sleep(2)

    # 3. Simulator
    start_process(f"{sys.executable} publisher_sim.py", "Sensor Simulator")
    
    print("\n✅ Simulation running.")
    print("Dashboard: http://localhost:5000")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            for p, name in processes:
                if p.poll() is not None:
                    print(f"⚠️ {name} exited unexpectedly with code {p.returncode}")
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
