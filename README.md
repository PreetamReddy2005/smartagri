# SmartAgri Fog Computing System

🌱 **Smart Agriculture Fog Computing Platform** - Real-time sensor monitoring, ML-powered irrigation control, and web visualization for precision farming.

## 📋 System Overview

The SmartAgri system implements a complete fog computing architecture for smart agriculture:

- **STM32 Hardware**: Real-time sensor data collection (moisture, temperature, pH, rainfall, water level)
- **MQTT Broker**: Lightweight messaging for IoT communication
- **Fog Processor**: ML-powered decision making and irrigation control
- **Web Dashboard**: Real-time visualization and manual control
- **Actuator Control**: Automated pump/valve management

### Architecture
```
STM32 Sensors → Serial → MQTT Bridge → MQTT Broker → Fog Processor → Actuators
                                      ↓
                               Web Dashboard ← Real-time Updates
```

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (recommended)
- **Python 3.8+** (for host components)
- **STM32 hardware** (optional, simulators available)

### Option 1: Automated Setup (Recommended)

1. **Run Setup Script**:
   ```bash
   python setup.py install
   ```

2. **Start System**:
   - **Windows**: Double-click `start_system.bat` or run `python smartagri_launcher.py`
   - **Linux/macOS**: Run `./run_all.sh` or `python smartagri_launcher.py`

3. **Access Dashboard**: Open http://localhost:5000

### Option 2: Manual Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Services**:
   ```bash
   docker-compose up --build -d
   ```

3. **Connect STM32** (optional):
   ```bash
   export SERIAL_PORT=/dev/ttyUSB0  # Adjust for your system
   python stm32_mqtt_bridge.py
   ```

4. **Access Dashboard**: http://localhost:5000

## 📁 Project Structure

```
smartagri/
├── docker-compose.yml          # Multi-service orchestration
├── Dockerfile                  # Python application container
├── requirements.txt            # Python dependencies
├── setup.py                    # Automated setup script
├── smartagri_launcher.py       # Intelligent launcher
├── start_system.bat            # Windows startup script
├── run_all.sh                  # Linux/macOS startup script
├── smartagri_config.json       # System configuration
├── .env                        # Environment variables
├── smartagri_logs/             # Application logs
│   ├── bridge.log
│   ├── processor.log
│   ├── visualizer.log
│   └── actuator.log
├── config/
│   └── mosquitto.conf          # MQTT broker configuration
├── templates/
│   └── dashboard.html          # Web dashboard template
├── stm32_src/                  # STM32 firmware source
├── bridge/
│   └── mqtt_bridge.js          # Alternative Node.js bridge
├── processor.py                # Fog processing node
├── visualizer.py               # Web dashboard server
├── ml_model.py                 # Machine learning models
├── stm32_mqtt_bridge.py        # Serial to MQTT bridge
├── publisher_sim.py            # Sensor data simulator
├── actuator_sim.py             # Actuator simulator
└── suggestions.py              # Crop recommendations
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file or export variables:

```bash
# Serial connection
SERIAL_PORT=/dev/ttyUSB0          # Linux/macOS
SERIAL_PORT=COM3                  # Windows

# MQTT settings
MQTT_BROKER=localhost
MQTT_PORT=1883

# Web dashboard
DASHBOARD_URL=http://localhost:5000

# Logging
LOG_DIR=./smartagri_logs
```

### Docker Compose Services

| Service | Purpose | Port | Dependencies |
|---------|---------|------|--------------|
| `mosquitto` | MQTT message broker | 1883 | - |
| `processor` | ML processing & decisions | - | mosquitto |
| `publisher` | Sensor data simulation | - | mosquitto |
| `actuator` | Pump/valve control | - | mosquitto, processor |
| `visualizer` | Web dashboard | 5000 | mosquitto, processor |

## 🖥️ Web Dashboard Features

- **Real-time Sensor Monitoring**: Live charts for moisture, temperature, pH
- **Irrigation Control**: Automatic and manual pump control
- **Crop Selection**: Dynamic ML model switching (tomatoes, lettuce, etc.)
- **Weather Integration**: Rainfall monitoring and predictions
- **Actuator Status**: Real-time pump/valve state display
- **Historical Data**: Last 100 sensor readings with timestamps

### API Endpoints

- `GET /` - Main dashboard
- `GET /api/sensor-data` - Recent sensor readings
- `GET /api/actuator-status` - Current actuator states
- `POST /api/crop-selection` - Change crop type

## 🔌 Hardware Integration

### STM32 Setup

1. **Flash Firmware**:
   ```bash
   cd stm32_src
   make
   # Flash using ST-Link or your programmer
   ```

2. **Serial Output Format**:
   ```
   moisture:45.2,temp:25.3,ph:6.8,rain:0,water_level:78.5
   ```

3. **Bridge Configuration**:
   - Baud rate: 115200
   - Data bits: 8
   - Stop bits: 1
   - Parity: None

### Alternative Bridges

- **Python Bridge**: `stm32_mqtt_bridge.py` (recommended)
- **Node.js Bridge**: `bridge/mqtt_bridge.js` (alternative)

## 🤖 Machine Learning Models

### Supported Crops
- Tomatoes
- Lettuce
- Spinach
- Strawberries

### Features
- **Irrigation Prediction**: Binary classification (needs water / doesn't need)
- **Moisture Forecasting**: 4-step ahead prediction
- **Water Consumption**: Estimated liters per irrigation cycle

### Model Training
```python
from ml_model import SmartAgriML

model = SmartAgriML()
model.train_model(crop_type='tomatoes')
```

## 📊 Monitoring & Troubleshooting

### Health Checks

1. **MQTT Broker**:
   ```bash
   docker-compose exec mosquitto mosquitto_pub -t test -m "hello"
   ```

2. **Web Dashboard**:
   ```bash
   curl http://localhost:5000
   ```

3. **Service Logs**:
   ```bash
   docker-compose logs -f processor
   ```

### Common Issues

#### Serial Connection Issues
```bash
# Check available ports
ls /dev/tty*          # Linux
ls /dev/cu.*          # macOS
wmic path Win32_SerialPort get DeviceID  # Windows

# Set permissions (Linux)
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0
```

#### Docker Network Issues
```bash
# Check container connectivity
docker-compose exec processor ping mosquitto

# Restart services
docker-compose down && docker-compose up --build -d
```

#### Python Import Errors
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Log Files
All logs are stored in `smartagri_logs/`:
- `bridge.log` - Serial to MQTT bridge
- `processor.log` - ML processing and decisions
- `visualizer.log` - Web server and MQTT subscriptions
- `actuator.log` - Pump/valve control actions

## 🔄 Development & Testing

### Running Tests
```bash
python setup.py test
```

### Development Mode
```bash
# Run individual components
python processor.py
python visualizer.py
python actuator_sim.py

# With MQTT broker
docker-compose up mosquitto -d
```

### Adding New Crops
1. Update `ml_model.py` with new crop data
2. Add to `CROPS` list in configuration
3. Retrain model with new data

## 📈 Performance Optimization

### Docker Optimization
- Use multi-stage builds for smaller images
- Mount volumes for development
- Configure resource limits in docker-compose.yml

### MQTT Optimization
- Use QoS 0 for real-time data
- Implement message persistence for critical commands
- Configure keep-alive intervals

### ML Optimization
- Use model quantization for edge deployment
- Implement batch processing for predictions
- Cache frequently used crop models

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request

### Code Standards
- Use type hints for Python functions
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: This README
- **Community**: GitHub Discussions

---

**Built with ❤️ for smart agriculture and IoT innovation**
