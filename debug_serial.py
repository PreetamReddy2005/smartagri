import serial.tools.list_ports
import serial
import time

def list_ports():
    print("Available ports:")
    ports = list(serial.tools.list_ports.comports())
    for i, p in enumerate(ports):
        print(f"{i}: {p.device} - {p.description}")
    return ports

def read_from_port(port_name, baud_rate=9600):
    print(f"\nAttempting to read from {port_name} at {baud_rate} baud...")
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=1)
        print("Connected! Waiting for data (Press Ctrl+C to stop)...")
        while True:
            if ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        print(f"Received: {line}")
                except UnicodeDecodeError:
                    print(f"Received (raw bytes): {ser.readline()}")
            time.sleep(0.1)
    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    ports = list_ports()
    if not ports:
        print("No serial ports found.")
    else:
        try:
            selection = int(input("\nSelect port number to monitor (e.g., 0): "))
            if 0 <= selection < len(ports):
                baud = input("Enter baud rate (default 9600): ")
                baud = int(baud) if baud.strip() else 9600
                read_from_port(ports[selection].device, baud)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input.")
