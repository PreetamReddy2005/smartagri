# STM32 Hardware Setup Guide

Complete guide for connecting and configuring STM32 sensors with the SmartAgri fog computing system.

## Overview

The STM32 microcontroller collects real-time sensor data and sends it to the fog computing system via serial communication.

**Sensor Types**:
- Soil moisture sensor
- Temperature sensor (DHT11/DHT22 or DS18B20)
- pH sensor
- Rain sensor
- Water level sensor

## Hardware Requirements

### STM32 Board
- **Recommended**: STM32F0 Discovery, STM32 Nucleo, or any STM32 board with UART
- Minimum 5 GPIO pins for sensors
- USB or Serial UART connection

### Sensors
- Capacitive soil moisture sensor (output: 0-3.3V or 0-5V)
- DHT22 temperature/humidity sensor
- Analog pH sensor module
- Rain sensor (digital or analog)
- Ultrasonic or float water level sensor

### Additional Components
- Breadboard and jumper wires
- 10kΩ resistors (pull-ups)
- USB cable (Mini/Micro USB depending on board)
- Power supply (optional: battery pack for field deployment)

## Wiring Diagram

```
STM32F0 Discovery Connections:
┌─────────────────────┐
│     STM32F0         │
│                     │
│  PA0 ← Moisture     │  Analog input
│  PA1 ← pH           │  Analog input
│  PA2 ← Water Level  │  Analog input
│  PA3 ← DHT22 Data   │  Digital I/O
│  PA4 ← Rain         │  Digital input
│                     │
│  PA9 → USART1 TX    │  To PC/Bridge
│  PA10← USART1 RX    │  From PC/Bridge
│                     │
│  GND ──────────────┐│  Common ground
│  3V3 ──────────────┘│  3.3V power
└─────────────────────┘
```

## Firmware Setup

### Option 1: Using Pre-compiled Firmware

1. **Download Firmware**
   - Locate firmware in: `stm32_src/`
   - File: `smartagri_sensor.bin` or `.hex`

2. **Flash with STM32 Cube Programmer**
   ```bash
   # Install STM32 Cube Programmer from ST website
   # Connect STM32 via USB
   # Open Cube Programmer
   # Select file and click "Download"
   ```

3. **Alternative: ST-Link Utility**
   - Connect ST-Link to SWDIO/SWCLK pins
   - Open ST-Link Utility
   - File → Open → Select .hex file
   - Target → Program & Verify

### Option 2: Building from Source

**Prerequisites**:
- STM32 Cube IDE or ARM GCC toolchain
- STM32 HAL library

**Build Steps**:

```bash
cd stm32_src

# Using STM32 Cube IDE:
# 1. Import project: File → Import → Existing Projects
# 2. Select stm32_src folder
# 3. Build: Project → Build All

# Using command line (if Makefile present):
make clean
make all

# Flash:
make flash
```

## Serial Data Format

The STM32 sends sensor data in JSON format every 5 seconds:

```json
{
  "moisture": 45.2,
  "temp": 25.3,
  "ph": 6.8,
  "rain": 0,
  "water_level": 78
}
```

**Alternative CSV Format** (also supported):
```
45.2,25.3,6.8,0,78
```

Where:
- `moisture`: 0-100% (percentage)
- `temp`: -40 to 80°C (temperature)
- `ph`: 0-14 (pH level)
- `rain`: 0 or 1 (binary: no rain/raining)
- `water_level`: 0-100% (tank level)

## Software Bridge Setup

### 1. Identify Serial Port

**Windows**:
```powershell
# Device Manager → Ports (COM & LPT)
# Note the COM port number (e.g., COM3, COM4)

# Or use PowerShell:
Get-WMIObject Win32_SerialPort | Select-Object Name,DeviceID
```

**Linux**:
```bash
# List all serial devices
ls /dev/tty*

# Check recently connected devices
dmesg | grep tty

# Common ports:
# /dev/ttyUSB0 - USB-to-Serial adapter
# /dev/ttyACM0 - Direct USB connection
```

**macOS**:
```bash
ls /dev/cu.*
# e.g., /dev/cu.usbserial-XXX or /dev/cu.usbmodem-XXX
```

### 2. Set Environment Variable

**Windows (PowerShell)**:
```powershell
$env:SERIAL_PORT="COM3"
$env:BAUD_RATE="115200"
```

**Linux/macOS**:
```bash
export SERIAL_PORT=/dev/ttyUSB0
export BAUD_RATE=115200
```

**Or create .env file**:
```bash
# In project root directory
echo "SERIAL_PORT=COM3" > .env
echo "BAUD_RATE=115200" >> .env
```

### 3. Run the Bridge

```bash
python stm32_mqtt_bridge.py
```

**Expected Output**:
```
============================================================
STM32 to MQTT Bridge - Smart Agriculture System
============================================================
Connecting to MQTT broker: localhost:1883
✅ Connected to MQTT broker
Opening serial port: COM3 at 115200 baud
✅ Serial connection established

🚀 Bridge running... Press Ctrl+C to stop

📤 Published: M:45.2% T:25.3°C pH:6.8 R:0 W:78%
📤 Published: M:44.8% T:25.5°C pH:6.7 R:0 W:77%
...
```

## Troubleshooting

### Serial Port Issues

**Error: "Serial error: could not open port"**

1. **Check port name**:
   ```bash
   # Windows
   mode
   
   # Linux
   ls -l /dev/ttyUSB*
   ```

2. **Port permissions (Linux)**:
   ```bash
   # Add user to dialout group
   sudo usermod -a -G dialout $USER
   
   # Or temporarily:
   sudo chmod 666 /dev/ttyUSB0
   
   # Logout and login again
   ```

3. **Port already in use**:
   - Close Arduino IDE, PuTTY, or other serial monitors
   - Kill stale processes: `pkill -f stm32_mqtt_bridge`

**Error: "Timeout" or no data received**

1. **Check baud rate** - Must match STM32 firmware (default: 115200)
2. **Verify wiring** - TX/RX might be swapped
3. **Test with serial monitor**:
   ```bash
   # Linux
   screen /dev/ttyUSB0 115200
   
   # Windows: Use PuTTY or Arduino Serial Monitor
   ```

### Data Validation Issues

**Warning: "Invalid moisture" or similar**

- Check sensor connections
- Verify sensor output voltage matches STM32 ADC range (0-3.3V)
- Use voltage divider if sensor outputs 5V

**CSV parsing errors**

Ensure STM32 sends:
- Comma-separated values
- Exactly 5 values per line
- Newline (`\n`) at end of line

## Testing Without Hardware

### Using Simulator

The project includes a data simulator:

```bash
# Publishes fake sensor data for testing
python publisher_sim.py
```

This sends realistic sensor readings without needing STM32 hardware.

### Manual MQTT Publish

Test the system with manual data:

```bash
# Using mosquitto_pub
docker-compose exec mosquitto mosquitto_pub \
  -t smartagri/sensor_data \
  -m '{"moisture":45,"temp":25,"ph":6.8,"rain":0,"water_level":80}'

# Or with Python
python -c "import paho.mqtt.publish as pub; pub.single('smartagri/sensor_data', '{\"moisture\":45,\"temp\":25,\"ph\":6.8,\"rain\":0,\"water_level\":80}', hostname='localhost')"
```

## Advanced Configuration

### Custom Sensor Calibration

Edit `stm32_mqtt_bridge.py` to add calibration:

```python
class SensorValidator:
    def validate_and_filter(self, data):
        # Add calibration offset
        moisture = data.get('moisture')
        if moisture is not None:
            moisture = moisture * 1.05 - 2.0  # Calibrate
            validated['moisture'] = round(moisture, 1)
        ...
```

### Changing Data Rate

**In STM32 firmware** (`main.c`):
```c
// Change delay in main loop
HAL_Delay(5000);  // Send every 5 seconds (default)
HAL_Delay(10000); // Send every 10 seconds
```

**Rebuild and reflash** after changes.

### Adding New Sensors

1. **Update STM32 firmware** to read new sensor
2. **Modify JSON output** in `snprintf()` call
3. **Update validator** in `stm32_mqtt_bridge.py`:
   ```python
   # Add new sensor field
   validated['new_sensor'] = data.get('new_sensor')
   ```

## Production Deployment

### Power Considerations
- Use 3.7V LiPo battery + voltage regulator for portable deployment
- Solar panel + battery for continuous field operation
- USB power bank for temporary testing

### Weatherproofing
- Use IP65 rated enclosure
- Seal sensor cables with silicone
- Elevate electronics above ground level

### Reliability
- Add watchdog timer in STM32 firmware
- Implement auto-reconnect in bridge script
- Use systemd service (Linux) or Task Scheduler (Windows) for auto-start

## Reference

### serial Communication Settings
- **Baud Rate**: 115200
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 1
- **Flow Control**: None

### Useful Commands

```bash
# List available ports
python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"

# Test serial communication
python -c "import serial; s=serial.Serial('COM3',115200,timeout=2); print(s.readline())"

# Monitor MQTT traffic
docker-compose exec mosquitto mosquitto_sub -t 'smartagri/#' -v
```

## Next Steps

- [STARTUP_GUIDE.md](file:///c:/Users/ASUS/Desktop/fog/STARTUP_GUIDE.md) - Run the complete system
- Configure crop types in dashboard
- Set up automated irrigation rules
- Monitor ML predictions in real-time
