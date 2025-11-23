@echo off
title SmartAgri Complete System Launcher
color 0A

echo ===================================================
echo       SmartAgri + Habitat Monitor Launcher
echo ===================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/5] Installing/Updating Dependencies...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies may not have installed correctly
)
echo.

echo [2/5] Starting MQTT Broker (Mosquitto)...
docker ps >nul 2>&1
if %errorlevel% equ 0 (
    echo Docker is running. Starting Mosquitto container...
    docker-compose up -d mosquitto
    timeout /t 2 >nul
) else (
    echo WARNING: Docker not running. MQTT broker may not start.
    echo          Install Docker Desktop and start it to enable MQTT.
)
echo.

echo [3/5] Launching Processor (ML Engine)...
start "SmartAgri Processor" cmd /k "python processor.py"
timeout /t 2 >nul
echo.

echo [4/5] Launching Visualizer (Web Server)...
start "SmartAgri Visualizer" cmd /k "python visualizer.py"
timeout /t 3 >nul
echo.

echo [5/5] Opening Dashboard in Browser...
timeout /t 5 >nul
start http://localhost:5000
echo.

echo ===================================================
echo         System Started Successfully!
echo ===================================================
echo.
echo Dashboards Available:
echo   - Main Dashboard:      http://localhost:5000
echo   - Habitat Monitor:     http://localhost:5000/habitat_monitor
echo   - Field Map:           http://localhost:5000/field_map
echo.
echo.
echo === Optional Components ===
echo.
echo [S] Start STM32 Bridge (Real Hardware Sensors)
echo [P] Start Publisher Simulator (Test Data)
echo [M] Standalone Habitat Monitor (Matplotlib)
echo [Q] Quit
echo.

:menu
choice /c SPMQ /n /m "Select option: "

if errorlevel 4 goto quit
if errorlevel 3 goto habitat
if errorlevel 2 goto publisher
if errorlevel 1 goto stm32

:stm32
echo.
echo Starting STM32 MQTT Bridge...
start "STM32 Bridge" cmd /k "python stm32_mqtt_bridge.py"
echo STM32 Bridge started in new window.
echo.
goto menu

:publisher
echo.
echo Starting Publisher Simulator...
start "Publisher Simulator" cmd /k "python publisher_sim.py"
echo Publisher Simulator started in new window.
echo.
goto menu

:habitat
echo.
echo Starting Standalone Habitat Monitor (Matplotlib)...
echo NOTE: Make sure PuTTY is CLOSED before running this!
start "Habitat Monitor" cmd /k "python habitat_monitor.py"
echo Habitat Monitor started in new window.
echo.
goto menu

:quit
echo.
echo To stop all services:
echo   1. Close all terminal windows
echo   2. Run: docker-compose down
echo.
echo Press any key to exit launcher...
pause >nul
exit
