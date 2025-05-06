import os
import csv
import sys
import math
import logging
from time import strftime, sleep, time
from serial import Serial
from pyubx2 import UBXReader, UBX_PROTOCOL, NMEA_PROTOCOL
from gpiozero import LED
from multiprocessing import Process, Value

# GPIO pin number for the GREEN LED
GREEN_LED_PIN = 17

# Open Csv file to read from it
# with open('recordedData.csv', 'r') as csvfile:
# open serial connection with high baud rate
# for every row that we read we need to process it
#
#

# Create the "Logs" directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), 'Logs')
os.makedirs(log_dir, exist_ok=True)

# Log file path with a unique name based on the current date
log_file = os.path.join(log_dir, f'recordDataToCsv_{strftime("%Y-%m-%d")}.log')

# Initialize logging with timestamp in every log message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='w'  # Overwrite the log file if it already exists
)

def flash_led(is_writing):
    """Controls the green LED based on the writing state."""
    green_led = LED(GREEN_LED_PIN)
    try:
        while True:
            if is_writing.value:  # If writing to the CSV file
                green_led.on()
            else:  # If not writing to the CSV file
                green_led.off()
            sleep(0.1)  # Check the state every 100ms
    except KeyboardInterrupt:
        pass
    finally:
        green_led.off()  # Ensure the LED is turned off on exit

def log_serial_data(mow_id, is_writing):
    """Logs specific fields from UBX and NMEA messages into a CSV file."""
    # Create the "Data" directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'Data')
    os.makedirs(data_dir, exist_ok=True)

    # Create a new CSV file with Mow ID and date/time in the filename
    filename = os.path.join(data_dir, f"{mow_id}_{strftime('%Y%m%d-%H%M%S')}_GPSData.csv")   

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write CSV header
        writer.writerow(['timestamp', 'latitude', 'longitude', 'speed', 'rel_north', 'rel_east', 'rel_down', 'heading'])

        # Initialize buffers for the latest values
        latest_latitude = latest_longitude = latest_speed = None
        latest_rel_north = latest_rel_east = latest_rel_down = latest_heading = None
        last_timestamp = None

        # Open the serial port
        with Serial('/dev/ttyAMA0', 57600, timeout=1) as stream:
            # Configure UBXReader to parse both UBX and NMEA messages
            ubr = UBXReader(stream, protfilter=UBX_PROTOCOL | NMEA_PROTOCOL)
            logging.info(f"Logging specific fields to {filename}. Press Ctrl+C to stop.")
            try:
                while True:
                    # Read and parse data
                    raw_data, parsed_data = ubr.read()
                    if parsed_data:
                        timestamp = strftime("%Y-%m-%d %H:%M:%S")

                        # Parse NMEA messages
                        if parsed_data.identity.startswith("GNRMC"):  # Recommended Minimum Navigation Information
                            latest_latitude = parsed_data.lat
                            latest_longitude = parsed_data.lon
                            latest_speed = float(parsed_data.spd) * 1.852 if parsed_data.spd else 0  # Convert knots to km/h
                            last_timestamp = timestamp
                            logging.info(f"latitude {latest_latitude}, longitude {latest_longitude}, speed {latest_speed} km/h")
                        # Parse UBX messages
                        if parsed_data.identity == "NAV-RELPOSNED":  # Relative Position NED
                            latest_rel_north = parsed_data.relPosN / 100  # Convert to meters
                            latest_rel_east = parsed_data.relPosE / 100   # Convert to meters
                            latest_rel_down = parsed_data.relPosD / 100   # Convert to meters
                            latest_heading = parsed_data.relPosHeading    # degrees
                            last_timestamp = timestamp

                            if latest_heading == 0.0:
                                latest_heading = math.degrees(math.atan2(latest_rel_east, latest_rel_north))
                                if latest_heading < 0:
                                    latest_heading += 360  # Normalize to 0-360 degrees

                            logging.info(f"latest_rel_north {latest_rel_north}, latest_rel_east {latest_rel_east}, latest_rel_down {latest_rel_down} latest_heading {latest_heading}")
                        
                        # Signal that we are writing to the CSV file
                        is_writing.value = 1
                        
                        # Write to CSV only if both NMEA and UBX data are available
                        if all([latest_latitude, latest_longitude, latest_speed, latest_rel_north, latest_rel_east, latest_rel_down, latest_heading]):
                            writer.writerow([last_timestamp, latest_latitude, latest_longitude, latest_speed, latest_rel_north, latest_rel_east, latest_rel_down, latest_heading])
                            csvfile.flush()

                            # Reset the buffer after writing
                            latest_latitude = latest_longitude = latest_speed = None
                            latest_rel_north = latest_rel_east = latest_rel_down = latest_heading = None
                    else:
                        # Signal that we are not writing to the CSV file
                        is_writing.value = 0
            except KeyboardInterrupt:
                logging.info("Logging stopped by user.")
            except Exception as e:
                logging.error(f"Error: {e}")
            finally:
                # Ensure the LED turns off when exiting
                is_writing.value = 0

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(1)
    combination = sys.argv[1]

    # Shared value to signal the LED process
    is_writing = Value('i', 0)  # Create a shared Value object (0 = not writing, 1 = writing)

    # Start the LED flashing process
    led_process = Process(target=flash_led, args=(is_writing,))
    led_process.start()

    try:
        # Start the main logging process
        log_serial_data(combination, is_writing)
    finally:
        # Ensure the LED process is terminated on exit
        is_writing.value = 0  # Turn off the LED
        led_process.terminate()
        led_process.join()