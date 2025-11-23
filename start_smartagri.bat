@echo off
title SmartAgri Launcher
color 0A

echo ===================================================
echo       SmartAgri System Automation Script
echo ===================================================
echo.

echo [1/3] Checking and installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies!
    pause
    exit /b
)
echo Dependencies are up to date.
echo.

echo [2/3] Launching SmartAgri System...
echo The dashboard will open automatically in 5 seconds.
echo.

:: Start the python script in the current window
:: We use start /B to run it in background but share stdout, 
:: OR just run it directly. Running directly is better to keep the window open for logs.
:: But we want to open the browser too.

:: Start browser in parallel after a delay
start /b "" cmd /c "timeout /t 5 >nul && start http://localhost:5000"

:: Run the main system
python manual_start.py

pause
