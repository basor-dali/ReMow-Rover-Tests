import os
import csv
import sys
from time import strftime, sleep, time
from serial import Serial
from pyubx2 import UBXReader, UBX_PROTOCOL, NMEA_PROTOCOL
from gpiozero import LED
from multiprocessing import Process

# GPIO pin number for the GREEN LED
GREEN_LED_PIN = 17

def flash_led():
    """Flashes the green LED every 5 seconds."""
    green_led = LED(GREEN_LED_PIN)
    try:
        while True:
            green_led.on()
            sleep(0.1)  # Keep the LED on for 100ms
            green_led.off()
            sleep(4.9)  # Wait for the remaining time to complete 5 seconds
    except KeyboardInterrupt:
        pass
    finally:
        green_led.off()  # Ensure the LED is turned off on exit

def log_serial_data(mow_id):
    """Logs specific fields from UBX and NMEA messages into a CSV file."""
    # Create the "Data" directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'Data')
    os.makedirs(data_dir, exist_ok=True)

    # Create a new CSV file with the current date/time in the filename
    # filename = os.path.join(data_dir, f"ParsedData_{strftime('%Y%m%d-%H%M%S')}.csv")
    # Create a new CSV file with Mow ID and date/time in the filename
    filename = os.path.join(data_dir, f"{mow_id}_{strftime('%Y%m%d-%H%M%S')}_GPSData.csv")   

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write CSV header
        writer.writerow(['timestamp', 'latitude', 'longitude', 'speed', 'rel_north', 'rel_east', 'rel_down', 'heading'])

        # Initialize buffers for the latest values
        latest_latitude = latest_longitude = latest_speed = None
        latest_rel_north = latest_rel_east = latest_rel_down = latest_heading = None

        # Open the serial port
        with Serial('/dev/ttyAMA0', 230400, timeout=1) as stream:
            # Configure UBXReader to parse both UBX and NMEA messages
            ubr = UBXReader(stream, protfilter=UBX_PROTOCOL | NMEA_PROTOCOL)
            print(f"Logging specific fields to {filename}. Press Ctrl+C to stop.")
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
                            latest_speed = float(parsed_data.spd) * 1.852  # Convert knots to km/h

                        # Parse UBX messages
                        if parsed_data.identity == "NAV-RELPOSNED":  # Relative Position NED
                            latest_rel_north = parsed_data.relPosN / 100  # Convert to meters
                            latest_rel_east = parsed_data.relPosE / 100   # Convert to meters
                            latest_rel_down = parsed_data.relPosD / 100   # Convert to meters
                            latest_heading = parsed_data.relPosHeading    # degrees

                        # Write to CSV only if both GNRMC and NAV-RELPOSNED data are available
                        if all([latest_latitude, latest_longitude, latest_speed, latest_rel_north, latest_rel_east, latest_rel_down, latest_heading]):
                            writer.writerow([timestamp, latest_latitude, latest_longitude, latest_speed, latest_rel_north, latest_rel_east, latest_rel_down, latest_heading])
                            csvfile.flush()
                            # print(f"{timestamp}, {latest_latitude}, {latest_longitude}, {latest_speed}, {latest_rel_north}, {latest_rel_east}, {latest_rel_down}, {latest_heading}")

                            # Reset the buffer after writing
                            latest_latitude = latest_longitude = latest_speed = None
                            latest_rel_north = latest_rel_east = latest_rel_down = latest_heading = None
            except KeyboardInterrupt:
                print("\nLogging stopped by user.")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(1)
    combination = sys.argv[1]

    # Start the LED flashing process
    led_process = Process(target=flash_led)
    led_process.start()

    try:
        # Start the main logging process
        log_serial_data(combination)
    finally:
        # Terminate the LED process on exit
        led_process.terminate()
        led_process.join()