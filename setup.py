#!/usr/bin/env python3
"""
SmartAgri Setup Script
======================

Automated setup and configuration for the SmartAgri system.
Handles dependency installation, environment setup, and initial configuration.

Usage:
    python setup.py [command]

Commands:
    install     Install all dependencies
    configure   Configure system settings
    test        Run system tests
    clean       Clean build artifacts
    help        Show this help message

Author: BlackBoxAI
Version: 1.0.0
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

class SmartAgriSetup:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.config_file = self.root_dir / "smartagri_config.json"
        self.requirements_file = self.root_dir / "requirements.txt"

    def print_banner(self):
        """Print setup banner"""
        banner = """
        ╔══════════════════════════════════════════════════════════════╗
        ║                    🌱 SmartAgri Setup 🌱                     ║
        ║              Automated Installation & Configuration          ║
        ╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def check_python_version(self):
        """Check if Python version is compatible"""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            print(f"Current version: {sys.version}")
            return False
        print(f"✅ Python {sys.version.split()[0]} detected")
        return True

    def install_python_dependencies(self):
        """Install Python dependencies"""
        print("\n📦 Installing Python dependencies...")

        if not self.requirements_file.exists():
            print("❌ requirements.txt not found")
            return False

        try:
            # Upgrade pip first
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True)

            # Install requirements
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)
            ], check=True)

            print("✅ Python dependencies installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Python dependencies: {e}")
            return False

    def check_docker(self):
        """Check Docker installation and status"""
        print("\n🐳 Checking Docker...")

        try:
            # Check Docker version
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"✅ {result.stdout.strip()}")
            else:
                raise subprocess.CalledProcessError(result.returncode, "docker --version")

            # Check Docker daemon
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print("✅ Docker daemon is running")
            else:
                print("⚠️  Docker daemon not running - please start Docker Desktop")
                return False

            # Check docker-compose
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"✅ {result.stdout.strip()}")
            else:
                print("❌ docker-compose not found")
                print("Please install Docker Compose")
                return False

            return True

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("❌ Docker not properly installed or not running")
            print("Please install Docker Desktop from https://www.docker.com/products/docker-desktop")
            return False

    def create_config(self):
        """Create default configuration file"""
        print("\n⚙️  Creating configuration...")

        default_config = {
            "version": "1.0.0",
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "topics": {
                    "sensor_data": "smartagri/sensor_data",
                    "actuator_commands": "smartagri/actuator_commands",
                    "crop_selection": "smartagri/crop_selection"
                }
            },
            "stm32": {
                "serial_ports": ["COM3", "COM4", "COM5", "/dev/ttyUSB0", "/dev/ttyACM0"],
                "baud_rate": 115200,
                "timeout": 2
            },
            "web": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            },
            "ml": {
                "model_path": "ml_model.pkl",
                "forecast_steps": 4,
                "crops": ["tomatoes", "lettuce", "spinach", "strawberries"]
            },
            "sensors": {
                "moisture_threshold": 40,
                "water_level_critical": 15,
                "temperature_ranges": {
                    "min": -10,
                    "max": 50
                },
                "ph_ranges": {
                    "min": 0,
                    "max": 14
                }
            }
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"✅ Configuration created: {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to create configuration: {e}")
            return False

    def verify_files(self):
        """Verify all required files exist"""
        print("\n📁 Verifying project files...")

        required_files = [
            "docker-compose.yml",
            "Dockerfile",
            "requirements.txt",
            "processor.py",
            "visualizer.py",
            "ml_model.py",
            "stm32_mqtt_bridge.py",
            "templates/dashboard.html"
        ]

        missing_files = []
        for file in required_files:
            if not (self.root_dir / file).exists():
                missing_files.append(file)

        if missing_files:
            print("❌ Missing required files:")
            for file in missing_files:
                print(f"  • {file}")
            return False

        print("✅ All required files present")
        return True

    def run_tests(self):
        """Run basic system tests"""
        print("\n🧪 Running system tests...")

        # Test imports
        try:
            import flask
            import paho.mqtt.client
            import sklearn
            import pandas
            import numpy
            print("✅ Python imports successful")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False

        # Test Docker services (build only)
        try:
            result = subprocess.run(
                ["docker-compose", "config"],
                capture_output=True, text=True, timeout=30,
                cwd=self.root_dir
            )
            if result.returncode == 0:
                print("✅ Docker Compose configuration valid")
            else:
                print("❌ Docker Compose configuration error")
                print(result.stderr)
                return False
        except subprocess.TimeoutExpired:
            print("❌ Docker Compose test timed out")
            return False

        print("✅ Basic tests passed")
        return True

    def create_startup_scripts(self):
        """Create platform-specific startup scripts"""
        print("\n🚀 Creating startup scripts...")

        # Windows batch script
        batch_content = '''@echo off
echo ========================================
echo Starting SmartAgri System
echo ========================================
echo.

echo Building and starting Docker services...
docker-compose up --build -d

echo.
echo Waiting for services to initialize...
timeout /t 15 /nobreak > nul

echo.
echo Checking service status...
docker-compose ps

echo.
echo Opening dashboard in browser...
start http://localhost:5000

echo.
echo ========================================
echo System Started Successfully!
echo ========================================
echo.
echo - Dashboard: http://localhost:5000
echo - MQTT Broker: localhost:1883
echo.
echo To stop the system, run: docker-compose down
echo To view logs, run: docker-compose logs -f
echo.
echo For STM32 connection:
echo 1. Flash the STM32 firmware
echo 2. Run: python stm32_mqtt_bridge.py
echo.
pause
'''

        # Linux/Mac shell script
        shell_content = '''#!/bin/bash

echo "========================================"
echo "Starting SmartAgri System"
echo "========================================"
echo

echo "Building and starting Docker services..."
docker-compose up --build -d

echo
echo "Waiting for services to initialize..."
sleep 15

echo
echo "Checking service status..."
docker-compose ps

echo
echo "Opening dashboard in browser..."
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5000
elif command -v open &> /dev/null; then
    open http://localhost:5000
else
    echo "Please open http://localhost:5000 in your browser"
fi

echo
echo "========================================"
echo "System Started Successfully!"
echo "========================================"
echo
echo "- Dashboard: http://localhost:5000"
echo "- MQTT Broker: localhost:1883"
echo
echo "To stop the system, run: docker-compose down"
echo "To view logs, run: docker-compose logs -f"
echo
echo "For STM32 connection:"
echo "1. Flash the STM32 firmware"
echo "2. Run: python stm32_mqtt_bridge.py"
echo
'''

        try:
            # Create Windows script
            with open(self.root_dir / "start_system.bat", 'w') as f:
                f.write(batch_content)
            print("✅ Created start_system.bat (Windows)")

            # Create Linux/Mac script
            with open(self.root_dir / "start_system.sh", 'w') as f:
                f.write(shell_content)
            print("✅ Created start_system.sh (Linux/Mac)")

            # Make shell script executable
            os.chmod(self.root_dir / "start_system.sh", 0o755)
            print("✅ Made start_system.sh executable")

            return True

        except Exception as e:
            print(f"❌ Failed to create startup scripts: {e}")
            return False

    def install(self):
        """Full installation process"""
        print("Starting SmartAgri installation...\n")

        steps = [
            ("Checking Python version", self.check_python_version),
            ("Verifying project files", self.verify_files),
            ("Checking Docker", self.check_docker),
            ("Installing Python dependencies", self.install_python_dependencies),
            ("Creating configuration", self.create_config),
            ("Running tests", self.run_tests),
            ("Creating startup scripts", self.create_startup_scripts)
        ]

        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"\n❌ Installation failed at: {step_name}")
                return False

        print("\n" + "="*60)
        print("🎉 SmartAgri installation completed successfully!")
        print("="*60)
        print("\n📋 Next steps:")
        print("1. Connect your STM32 hardware (optional)")
        print("2. Run: python smartagri_launcher.py")
        print("3. Or use: ./start_system.sh (Linux/Mac) or start_system.bat (Windows)")
        print("4. Open http://localhost:5000 in your browser")
        print("\n📖 For help, see README.md or run: python setup.py help")

        return True

    def configure(self):
        """Interactive configuration"""
        print("SmartAgri Configuration")
        print("="*30)

        if not self.config_file.exists():
            print("No existing configuration found. Creating default...")
            if not self.create_config():
                return False

        # Load current config
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return False

        print("Current configuration:")
        print(json.dumps(config, indent=2))

        # TODO: Add interactive configuration options
        print("\nConfiguration is currently set to defaults.")
        print("Edit smartagri_config.json manually for custom settings.")

        return True

    def clean(self):
        """Clean build artifacts"""
        print("Cleaning build artifacts...")

        patterns = [
            "*.pyc", "__pycache__", "*.log", ".pytest_cache",
            "*.egg-info", "dist", "build"
        ]

        cleaned = 0
        for pattern in patterns:
            for path in self.root_dir.rglob(pattern):
                if path.is_file():
                    path.unlink()
                    cleaned += 1
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                    cleaned += 1

        # Clean Docker
        try:
            subprocess.run(["docker", "system", "prune", "-f"], capture_output=True)
            print("✅ Docker system cleaned")
        except:
            pass

        print(f"✅ Cleaned {cleaned} artifacts")
        return True

    def help(self):
        """Show help information"""
        print(__doc__)

def main():
    parser = argparse.ArgumentParser(
        description="SmartAgri Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "command",
        choices=["install", "configure", "test", "clean", "help"],
        default="help",
        nargs="?",
        help="Command to execute"
    )

    args = parser.parse_args()

    setup = SmartAgriSetup()

    if args.command == "help":
        setup.help()
    elif args.command == "install":
        setup.print_banner()
        success = setup.install()
    elif args.command == "configure":
        success = setup.configure()
    elif args.command == "test":
        success = setup.run_tests()
    elif args.command == "clean":
        success = setup.clean()
    else:
        setup.help()
        success = True

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
