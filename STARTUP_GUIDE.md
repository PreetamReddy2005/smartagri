# SmartAgri Quick Startup Guide

Get your SmartAgri fog computing system up and running in minutes.

## Prerequisites

- **Docker Desktop** installed and running
- **Python 3.8+** installed
- **Git** (optional, for cloning)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web server)
- paho-mqtt (MQTT client)
- scikit-learn (ML models)
- pandas, numpy (data processing)
- flask-socketio, flask-cors (real-time updates)
- pyserial (STM32 communication)

### 2. Verify Docker

Make sure Docker Desktop is running:

```bash
docker --version
docker-compose --version
```

## Running the System

### Option 1: Automated Launcher (Recommended)

**Windows:**
```bash
python smartagri_launcher.py
```

**Linux/macOS:**
```bash
./run_all.sh
```

This will:
- Start MQTT broker (Mosquitto)
- Launch fog processor with ML models
- Start sensor data simulator
- Open web dashboard at http://localhost:5000

### Option 2: Manual Start

**Step 1: Start Docker Services**
```bash
docker-compose up --build -d
```

**Step 2: Start Python Components**

Open separate terminal windows for each:

```bash
# Terminal 1: Processor (ML + Decision Engine)
python processor.py

# Terminal 2: Visualizer (Web Dashboard)
python visualizer.py

# Terminal 3: Actuator Simulator
python actuator_sim.py
```

**Step 3: (Optional) Connect STM32**

If you have STM32 hardware:
```bash
python stm32_mqtt_bridge.py
```

See [STM32_SETUP.md](file:///c:/Users/ASUS/Desktop/fog/STM32_SETUP.md) for detailed hardware setup.

## Accessing the System

### Web Dashboard
Open your browser and go to:
```
http://localhost:5000
```

You should see:
- Real-time sensor charts (moisture, temperature, pH)
- ML predictions and forecasts
- Crop selection dropdown
- Irrigation control
- AI insights panel

### MQTT Broker
- **Host**: localhost
- **Port**: 1883
- **Topics**:
  - `smartagri/sensor_data` - Sensor readings
  - `smartagri/actuator_command` - Pump commands
  - `smartagri/fog_status` - System status

## Testing the System

### 1. Check Services Status

```bash
docker-compose ps
```

All services should show "Up".

### 2. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f processor
```

### 3. Test with Simulator

The publisher simulator sends random sensor data every 5 seconds. Watch the dashboard update in real-time.

### 4. Change Crop Type

In the dashboard, select a different crop (lettuce, spinach, etc.) from the dropdown. You should see:
- Updated optimal ranges
- Crop-specific suggestions
- Adjusted irrigation thresholds

## Troubleshooting

### Dashboard Not Loading
```bash
# Check if visualizer is running
curl http://localhost:5000

# Restart visualizer
python visualizer.py
```

### MQTT Connection Failed
```bash
# Check if Mosquitto is running
docker-compose ps mosquitto

# Restart MQTT broker
docker-compose restart mosquitto
```

### No Sensor Data
```bash
# Check publisher logs
docker-compose logs publisher

# Manually publish test data
docker-compose exec mosquitto mosquitto_pub -t smartagri/sensor_data -m '{"moisture":45,"temp":25,"ph":6.8,"rain":false,"water_level":80}'
```

### Python Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Stopping the System

**Graceful Shutdown:**
```bash
docker-compose down
```

**Force Stop:**
```bash
docker-compose down -v
# Press Ctrl+C in each Python terminal
```

## Next Steps

- [STM32_SETUP.md](file:///c:/Users/ASUS/Desktop/fog/STM32_SETUP.md) - Connect real hardware sensors
- [README.md](file:///c:/Users/ASUS/Desktop/fog/README.md) - Full documentation
- Configure crop profiles in `suggestions.py`
- Customize ML model parameters in `ml_model.py`

## Quick Reference

| Component | Port | Command |
|-----------|------|---------|
| Dashboard | 5000 | `python visualizer.py` |
| MQTT Broker | 1883 | `docker-compose up mosquitto` |
| Processor | - | `python processor.py` |
| Actuator | - | `python actuator_sim.py` |

## Support

- Check logs in `smartagri_logs/` directory
- Review test results: `python -m unittest discover tests`
- Verify configuration: `smartagri_config.json`
