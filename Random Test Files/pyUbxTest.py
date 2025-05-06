import os
import csv
from time import strftime
from serial import Serial
from pyubx2 import UBXReader, UBX_PROTOCOL, NMEA_PROTOCOL

def log_serial_data():
    """Logs specific fields from UBX and NMEA messages into a CSV file."""
    # Create the "Data" directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'Data')
    os.makedirs(data_dir, exist_ok=True)

    # Create a new CSV file with the current date/time in the filename
    filename = os.path.join(data_dir, f"ParsedData_{strftime('%Y%m%d-%H%M%S')}.csv")

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write CSV header
        writer.writerow(['timestamp', 'latitude', 'longitude', 'speed', 'rel_north', 'rel_east', 'rel_down', 'heading'])

        # Open the serial port 57600
        # with Serial('/dev/ttyAMA0', 230400, timeout=1) as stream:
        with Serial('/dev/ttyAMA0', 57600,timeout=1)as stream:
            # Configure UBXReader to parse both UBX and NMEA messages
            ubr = UBXReader(stream, protfilter=UBX_PROTOCOL | NMEA_PROTOCOL)
            print(f"Logging specific fields to {filename}. Press Ctrl+C to stop.")
            try:
                while True:
                    # Read and parse data
                    raw_data, parsed_data = ubr.read()
                    if parsed_data:
                        timestamp = strftime("%Y-%m-%d %H:%M:%S")
                        # Initialize fields
                        latitude = longitude = speed = rel_north = rel_east = rel_down = heading = None

                        # Parse NMEA messages
                        if parsed_data.identity.startswith("GNRMC"):  # Recommended Minimum Navigation Information
                            latitude = parsed_data.lat
                            longitude = parsed_data.lon
                            speed = float(parsed_data.spd) * 1.852  # Convert knots to km/h

                        # Parse UBX messages
                        if parsed_data.identity == "NAV-RELPOSNED":  # Relative Position NED
                            rel_north = parsed_data.relPosN / 100  # Convert to meters
                            rel_east = parsed_data.relPosE / 100   # Convert to meters
                            rel_down = parsed_data.relPosD / 100   # Convert to meters
                            heading = parsed_data.relPosHeading
                            print(f"DEBUG: NAV-RELPOSNED - rel_north={rel_north} m, rel_east={rel_east} m, rel_down={rel_down} m, heading={heading}°")

                        # Write to CSV only if all fields have valid data
                        if any([latitude, longitude, speed, rel_north, rel_east, rel_down, heading]):
                            writer.writerow([timestamp, latitude, longitude, speed, rel_north, rel_east, rel_down, heading])
                            csvfile.flush()
                            print(f"{timestamp}, {latitude}, {longitude}, {speed}, {rel_north}, {rel_east}, {rel_down}, {heading}")
            except KeyboardInterrupt:
                print("\nLogging stopped by user.")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == '__main__':
    log_serial_data()