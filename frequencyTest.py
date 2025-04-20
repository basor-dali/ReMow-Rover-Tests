import serial
import csv
import os
from time import strftime
import pynmea2
import psutil  # Import psutil for CPU usage monitoring

def log_gngga():
    """Logs parsed GNGGA messages and CPU usage to a CSV file with timestamps."""
    # Create the "Data" directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'Data')
    os.makedirs(data_dir, exist_ok=True)

    # Create a new CSV file with the current date/time in the filename
    filename = os.path.join(data_dir, f"1Hz_57600_with_CPU_LOG_GNGGA_{strftime('%Y%m%d-%H%M%S')}.csv")

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write CSV header with relevant GNGGA fields and CPU usage
        writer.writerow([
            'timestamp', 'raw_gngga', 'latitude', 'longitude', 'altitude', 
            'num_satellites', 'horizontal_dilution', 'fix_quality', 'cpu_usage'
        ])

        # Open the serial port
        with serial.Serial('/dev/ttyAMA0', baudrate=230400, timeout=1) as port:
            print(f"Logging GNGGA messages and CPU usage to {filename}. Press Ctrl+C to stop.")
            try:
                while True:
                    # Read a line from the serial port
                    data = port.readline().decode('ascii', errors='replace').strip()
                    if data.startswith('$GNGGA'):  # Only process GNGGA messages
                        timestamp = strftime("%Y-%m-%d %H:%M:%S")
                        try:
                            # Parse the GNGGA message
                            msg = pynmea2.parse(data)
                            # Get current CPU usage
                            cpu_usage = psutil.cpu_percent(interval=.1)  # Get CPU usage over 1 second
                            # Write data to CSV
                            writer.writerow([
                                timestamp, data, msg.latitude, msg.longitude, 
                                msg.altitude, msg.num_sats, msg.horizontal_dil, 
                                msg.gps_qual, cpu_usage
                            ])
                            csvfile.flush()
                            print(f"{timestamp}, {data}, {msg.latitude}, {msg.longitude}, {msg.altitude}, {msg.num_sats}, {msg.horizontal_dil}, {msg.gps_qual}, {cpu_usage}%")
                        except pynmea2.ParseError as e:
                            print(f"Parse error: {e}")
            except KeyboardInterrupt:
                print("\nLogging stopped by user.")

if __name__ == '__main__':
    log_gngga()