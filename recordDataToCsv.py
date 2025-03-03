import serial
import json
from ublox_gps import UbloxGps  # Corrected import statement
from time import strftime, sleep, time
import csv
import logging
import sys
import os
import gpiozero
from gpiozero import LED
import random

# GPIO pin number for the GREEN LED
GREEN_LED_PIN = 17

# Create the "Logs" directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), 'Logs')
os.makedirs(log_dir, exist_ok=True)

# Log file path with a unique name based on the current timestamp
log_file = os.path.join(log_dir, f'recordDataToCsv_{strftime("%Y%m%d-%H%M%S")}.log')

# Initialize logging with timestamp in every log message
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_file, filemode='w')

# Function to initialize the GREEN_LED with retries
def initialize_green_led(retries=3, delay=1):
    for attempt in range(retries):
        try:
            green_led = LED(GREEN_LED_PIN)
            return green_led
        except gpiozero.exc.GPIOPinInUse:
            logging.error(f"GPIO pin {GREEN_LED_PIN} is already in use, attempt {attempt + 1} of {retries}")
            sleep(delay)
        except Exception as e:
            logging.error(f"Unexpected error initializing GREEN_LED: {e}")
            return None
    return None

# Function to cleanup GPIO
def cleanup_gpio(led):
    if led:
        try:
            led.off()
        except gpiozero.exc.GPIODeviceClosed:
            logging.warning("Attempted to turn off an already closed or uninitialized LED")
        finally:
            led.close()

# Function to extract GPS data with error handling
def extract_gps_data(gps):
    try:
        coords = gps.geo_coords()  # Get geographic coordinates
        rel_pos = gps.request_standard_packet('NAV', 'RELPOSNED')  # Get relative position in NED coordinates

        # Log the coords and rel_pos objects
        logging.info(f"coords: {coords}")
        logging.info(f"rel_pos: {rel_pos}")

        # Extract data with error handling
        latitude = coords.lat if coords else None  # degrees
        longitude = coords.lon if coords else None  # degrees
        speed = coords.gSpeed if coords else None  # speed (mm/s)
        rel_north = (rel_pos.relPosN / 100) if hasattr(rel_pos, 'relPosN') else None  # relative North (m)
        rel_east = (rel_pos.relPosE / 100) if hasattr(rel_pos, 'relPosE') else None  # relative East (m)
        rel_down = (rel_pos.relPosD / 100) if hasattr(rel_pos, 'relPosD') else None  # relative Down (m)
        heading = rel_pos.relPosHeading if hasattr(rel_pos, 'relPosHeading') else None  # heading (degrees)

        # Convert speed from mm/s to m/s
        speed = speed / 1000 if speed is not None else None

        # Capture the current timestamp
        current_time = strftime("%Y-%m-%d %H:%M:%S")

        # Create a dictionary with the telemetry data
        telemetry = {
            "timestamp": current_time,  # timestamp
            "latitude": latitude,  # degrees
            "longitude": longitude,  # degrees
            "speed": speed,  # speed (m/s)
            "rel_north": rel_north,  # relative North (m)
            "rel_east": rel_east,  # relative East (m)
            "rel_down": rel_down,  # relative Down (m)
            "heading": heading  # heading (degrees)
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
        fieldnames = ['timestamp', 'latitude', 'longitude', 'speed', 'rel_north', 'rel_east', 'rel_down', 'heading']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write the header row

        # Open serial port connection
        with serial.Serial('/dev/ttyAMA0', baudrate=38400, timeout=1) as port:
            gps = UbloxGps(port)  # Initialize GPS object
            green_led = initialize_green_led()
            if green_led:
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
                            try:
                                green_led.on()
                                sleep(0.1)
                                green_led.off()
                            except Exception as e:
                                logging.error(f"Error initializing GPIO: {e}")
                        
                        # Calculate the elapsed time and adjust the sleep duration
                        elapsed_time = time() - start_time
                        logging.info(f"Elapsed time for this iteration: {elapsed_time:.2f} seconds")
                        sleep_duration = max(0, 1 - elapsed_time)
                        logging.info(f"Sleeping for: {sleep_duration:.2f} seconds")
                        sleep(sleep_duration)  # Wait for the remaining time to complete 1 second

                except KeyboardInterrupt:
                    logging.info("Program interrupted by user")
                except Exception as e:
                    logging.error(f"Unexpected error: {e}")
                finally:
                    cleanup_gpio(green_led)
            else:
                logging.error("Failed to initialize GREEN_LED, proceeding without LED")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logging.error("Usage: python3 recordDataToCsv.py <combination>")
        sys.exit(1)
    combination = sys.argv[1]
    logging.info(f"Generated Mow ID: {combination}")
    
    run(combination)  # Run the main function with the generated Mow ID