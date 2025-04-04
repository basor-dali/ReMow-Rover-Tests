import serial
import time

port = serial.Serial('/dev/ttyAMA0', baudrate=115200, timeout=1)

count = 0
start_time = time.time()

while True:
    data = port.readline().decode('ascii', errors='replace').strip()
    if data:
        count += 1
        print(data)
    elapsed_time = time.time() - start_time
    if elapsed_time >= 1:  # Check every second
        print(f"Messages per second: {count}")
        count = 0
        start_time = time.time()