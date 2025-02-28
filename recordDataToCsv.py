import serial
import json
from ublox_gps import UbloxGps
from time import strftime, sleep
import csv
import logging
import sys

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to extract GPS data with error handling
def extract_gps_data(gps):
    try:
        coords = gps.geo_coords()  # Get geographic coordinates
        hp_coords = gps.hp_geo_coords()  # Get high precision geographic coordinates

        # Extract data with error handling
        latitude = coords.lat if coords else None  # degrees
        longitude = coords.lon if coords else None  # degrees
        relPosN = (hp_coords.relPosHPN / 1000) if hp_coords else None  # meters (m)
        relPosE = (hp_coords.relPosHPE / 1000) if hp_coords else None  # meters (m)
        relPosD = (hp_coords.relPosHPD / 1000) if hp_coords else None  # meters (m)
        relPosLength = (hp_coords.relPosHPLength / 1000) if hp_coords else None  # meters (m)
        relPosHeading = hp_coords.relPosHeading if hp_coords else None  # degrees
        velN = (hp_coords.velN / 1000) if hp_coords else None  # meters per second (m/s)
        velE = (hp_coords.velE / 1000) if hp_coords else None  # meters per second (m/s)
        velD = (hp_coords.velD / 1000) if hp_coords else None  # meters per second (m/s)
        speed = (hp_coords.speed / 1000) if hp_coords else None  # meters per second (m/s)

        # Capture the current timestamp
        current_time = strftime("%Y-%m-%d %H:%M:%S")

        # Create a dictionary with the telemetry data
        telemetry = {
            "timestamp": current_time,  # timestamp
            "latitude": latitude,  # degrees
            "longitude": longitude,  # degrees
            "relPosN": relPosN,  # meters (m)
            "relPosE": relPosE,  # meters (m)
            "relPosD": relPosD,  # meters (m)
            "relPosLength": relPosLength,  # meters (m)
            "relPosHeading": relPosHeading,  # degrees
            "velN": velN,  # meters per second (m/s)
            "velE": velE,  # meters per second (m/s)
            "velD": velD,  # meters per second (m/s)
            "speed": speed  # meters per second (m/s)
        }
        return telemetry
    except AttributeError as e:
        logging.error(f"Error retrieving data: {e}")
        return None

# Main function to run the GPS data logging
def run(mow_id):
    logging.info("Listening for UBX Messages.")
    # Create a new CSV file with Mow ID and date/time in the filename
    filename = f"{mow_id}_{strftime('%Y%m%d-%H%M%S')}_GPSData.csv"
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'latitude', 'longitude', 'relPosN', 'relPosE', 'relPosD', 'relPosLength', 'relPosHeading', 'velN', 'velE', 'velD', 'speed']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write the header row

        # Open serial port connection
        with serial.Serial('/dev/ttyAMA0', baudrate=38400, timeout=1) as port:
            gps = UbloxGps(port)  # Initialize GPS object
            try:
                while True:
                    telemetry = extract_gps_data(gps)  # Extract GPS data
                    if telemetry:
                        # Write data to CSV
                        writer.writerow(telemetry)
                        csvfile.flush()  # Ensure data is written to the file
                        logging.info(f"Data written to CSV: {telemetry}")
                    sleep(1)  # Wait for 1 second before recording the next set of data

            except KeyboardInterrupt:
                logging.info("Program interrupted by user")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python recordDataToCsv.py <MowID>")
        sys.exit(1)
    mow_id = sys.argv[1]
    run(mow_id)  # Run the main function with the provided Mow ID