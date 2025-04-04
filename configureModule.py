import serial
import time

# Configure the serial port
serial_port = '/dev/ttyAMA0'  # Update to your port
baud_rate = 9600              # Update if needed

ser = serial.Serial(serial_port, baud_rate, timeout=1)
config_command = '$PUBX,40,GGA,0,5,0,0,0,0*5A\r\n'
ser.write(config_command.encode())
time.sleep(0.1)

# Read the response as raw bytes
response_bytes = ser.readline()
# Print the response in a hex dump format
print("Response (hex):", response_bytes.hex())

ser.close()