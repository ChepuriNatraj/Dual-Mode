import serial
import time
import sys

# Replace with your actual port if it's different, e.g., '/dev/ttyUSB0'
PORT = '/dev/ttyUSB0'
BAUD = 115200

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2) # Wait for ESP32 to reboot after connection
    print(f"Successfully connected to {PORT}")
    print("--------------------------------------------------")
    print("Enter 6 comma-separated angles (0 to 180) to move the arm.")
    print("Example: 90,90,90,90,90,90")
    print("Type 'exit' to quit.")
    print("--------------------------------------------------")

    while True:
        command = input("Enter angles (J0,J1,J2,J3,J4,J5): ")
        
        if command.lower() == 'exit':
            break
            
        # Add newline character which the ESP32 expects
        command += '\n'
        ser.write(command.encode('utf-8'))
        
        # Read the "OK" response from the ESP32
        response = ser.readline().decode('utf-8').strip()
        print(f"ESP32 Status: {response}")

except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    print("Make sure the port is correct and you have permission to access it.")
