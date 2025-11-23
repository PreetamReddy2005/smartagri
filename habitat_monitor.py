import serial
import json
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import time

# --- CONFIGURATION ---
SERIAL_PORT = 'COM8'  # <--- CHANGE THIS TO YOUR PORT!
BAUD_RATE = 38400     # Match your STM32 settings

# --- SETUP DATA STORAGE ---
# We keep the last 100 data points for a smooth graph
MAX_POINTS = 100
timestamps = deque(maxlen=MAX_POINTS)
temp_data = deque(maxlen=MAX_POINTS)
hum_data = deque(maxlen=MAX_POINTS)
soil_data = deque(maxlen=MAX_POINTS)

# --- SETUP PLOT ---
plt.style.use('dark_background') # Looks "Hacker/Conference" style
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
fig.suptitle('MUSHROOM HABITAT DIGITAL TWIN (LIVE)', color='#00ff00', fontsize=16)

# Configure the serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT}...")
except:
    print(f"ERROR: Could not open {SERIAL_PORT}. Is PuTTY still open?")
    exit()

def animate(i):
    # Read one line from STM32
    if ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8').strip()
            # Parse JSON: {"t":25.5,"h":60.2...}
            data = json.loads(line)
            
            # Store Data
            timestamps.append(time.time())
            temp_data.append(data['t'])
            hum_data.append(data['h'])
            # Invert Soil (4095 is dry, 0 is wet) -> Map to approx 0-100%
            soil_percent = 100 - (int(data['s']) * 100 / 4095)
            soil_data.append(soil_percent)

        except (json.JSONDecodeError, ValueError):
            pass # Ignore corrupt packets

    # Clear and Redraw Plots
    ax1.clear()
    ax2.clear()
    ax3.clear()

    # Plot 1: Temperature
    ax1.plot(temp_data, color='#ff5555', linewidth=2)
    ax1.set_ylabel('Temp (°C)')
    ax1.text(0.02, 0.9, f"Current: {temp_data[-1] if temp_data else 0} °C", transform=ax1.transAxes, color='white')

    # Plot 2: Humidity
    ax2.plot(hum_data, color='#5555ff', linewidth=2)
    ax2.set_ylabel('Humidity (%)')
    ax2.text(0.02, 0.9, f"Current: {hum_data[-1] if hum_data else 0} %", transform=ax2.transAxes, color='white')

    # Plot 3: Soil Moisture
    ax3.plot(soil_data, color='#55ff55', linewidth=2)
    ax3.set_ylabel('Soil Moisture (%)')
    ax3.set_ylim(0, 100)
    
    # "Conference Level" Anomaly Detection
    # If Soil Moisture drops below 20%, flash the screen red (simulated)
    if soil_data and soil_data[-1] < 20:
        ax3.set_facecolor('#330000') # Dark Red background alert
        ax3.text(0.5, 0.5, "CRITICAL: SOIL DRY", transform=ax3.transAxes, 
                 color='red', fontsize=20, ha='center', weight='bold')
    else:
        ax3.set_facecolor('black')

# Run the animation
ani = FuncAnimation(fig, animate, interval=100) # Update every 100ms
plt.show()
