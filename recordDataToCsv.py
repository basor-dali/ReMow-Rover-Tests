import serial
import json
from ublox_gps import UbloxGps
from time import strftime, sleep, time
import csv
import logging
import sys
import os
from gpiozero import LED
import random

# GPIO pin number for the GREEN LED
GREEN_LED = LED(17)

# Create the "Logs" directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), 'Logs')
os.makedirs(log_dir, exist_ok=True)

# Log file path with a unique name based on the current timestamp
log_file = os.path.join(log_dir, f'recordDataToCsv_{strftime("%Y%m%d-%H%M%S")}.log')

# Initialize logging with timestamp in every log message
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_file, filemode='w')

# Function to extract GPS data with error handling
def extract_gps_data(gps):
    try:
        coords = gps.geo_coords()  # Get geographic coordinates
        hp_coords = gps.hp_geo_coords()  # Get high precision geographic coordinates

        # Log the coords and hp_coords objects
        logging.info(f"coords: {coords}")
        logging.info(f"hp_coords: {hp_coords}")

        # Extract data with error handling
        latitude = coords.lat if coords else None  # degrees
        longitude = coords.lon if coords else None  # degrees
        height = hp_coords.height if hasattr(hp_coords, 'height') else None  # height above ellipsoid (mm)
        hMSL = hp_coords.hMSL if hasattr(hp_coords, 'hMSL') else None  # height above mean sea level (mm)
        heightHp = hp_coords.heightHp if hasattr(hp_coords, 'heightHp') else None  # high precision height above ellipsoid (mm)
        hMSLHp = hp_coords.hMSLHp if hasattr(hp_coords, 'hMSLHp') else None  # high precision height above mean sea level (mm)
        hAcc = hp_coords.hAcc if hasattr(hp_coords, 'hAcc') else None  # horizontal accuracy (mm)
        vAcc = hp_coords.vAcc if hasattr(hp_coords, 'vAcc') else None  # vertical accuracy (mm)

        # Capture the current timestamp
        current_time = strftime("%Y-%m-%d %H:%M:%S")

        # Create a dictionary with the telemetry data
        telemetry = {
            "timestamp": current_time,  # timestamp
            "latitude": latitude,  # degrees
            "longitude": longitude,  # degrees
            "height": height,  # height above ellipsoid (mm)
            "hMSL": hMSL,  # height above mean sea level (mm)
            "heightHp": heightHp,  # high precision height above ellipsoid (mm)
            "hMSLHp": hMSLHp,  # high precision height above mean sea level (mm)
            "hAcc": hAcc,  # horizontal accuracy (mm)
            "vAcc": vAcc  # vertical accuracy (mm)
        }
        return telemetry
    except AttributeError as e:
        logging.error(f"Error retrieving data: {e}")
        return None

# Function to generate a random 2-digit Mow ID
def generate_mow_id():
    return f"{random.randint(10, 99)}"

# Main function to run the GPS data logging
def run(mow_id):
    logging.info("Listening for UBX Messages.")
    
    # Create the "Data" directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'Data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Create a new CSV file with Mow ID and date/time in the filename
    filename = os.path.join(data_dir, f"{mow_id}_{strftime('%Y%m%d-%H%M%S')}_GPSData.csv")
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'latitude', 'longitude', 'height', 'hMSL', 'heightHp', 'hMSLHp', 'hAcc', 'vAcc']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write the header row

        # Open serial port connection
        with serial.Serial('/dev/ttyAMA0', baudrate=38400, timeout=1) as port:
            gps = UbloxGps(port)  # Initialize GPS object
            try:
                while True:
                    start_time = time()  # Record the start time of the loop
                    telemetry = extract_gps_data(gps)  # Extract GPS data
                    if telemetry:
                        # Write data to CSV
                        writer.writerow(telemetry)
                        csvfile.flush()  # Ensure data is written to the file
                        logging.info(f"Data written to CSV: {telemetry}")
                        
                        # Flash GREEN LED
                        GREEN_LED.on()
                        sleep(0.1)
                        GREEN_LED.off()
                    
                    # Calculate the elapsed time and adjust the sleep duration
                    elapsed_time = time() - start_time
                    logging.info(f"Elapsed time for this iteration: {elapsed_time:.2f} seconds")
                    sleep(max(0, 1 - elapsed_time))  # Wait for the remaining time to complete 1 second

            except KeyboardInterrupt:
                logging.info("Program interrupted by user")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
            finally:
                pass  # No need to clean up GPIO with gpiozero

if __name__ == '__main__':
    # Generate a random 2-digit Mow ID
    mow_id = generate_mow_id()
    logging.info(f"Generated Mow ID: {mow_id}")
    
    run(mow_id)  # Run the main function with the generated Mow ID