import serial
import time

# Configure the serial port
ser = serial.Serial('/dev/ttyAMA0', 38400, timeout=1)

# Open a log file
log_file = open('zed_f9p_log.txt', 'w')

# Start time
start_time = time.time()

# Log messages for 60 seconds
while time.time() - start_time < 60:
    try:
        # Read a line from the serial port
        line = ser.readline().decode('utf-8').strip()
        
        # Log the message with a timestamp
        if line:
            log_file.write(f'{time.time()} - {line}\n')
            
    except UnicodeDecodeError:
        # Ignore decode errors
        pass

# Close the log file and serial port
log_file.close()
ser.close()

# Print the contents of the log file
with open('zed_f9p_log.txt', 'r') as log_file:
    print(log_file.read())