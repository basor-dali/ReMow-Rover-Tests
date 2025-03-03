import time
import configparser
import os
import serial
from ublox_gps import UbloxGps  # Assuming you have a library for Ublox GPS
from datetime import datetime
import csv
import math
from gpiozero import LED
from signal import pause

config = configparser.ConfigParser()
config_path = '/etc/thingsboard_config.ini'
config.read(config_path)

# Initialize GPS and serial connection
port = serial.Serial('/dev/ttyAMA0', baudrate=38400, timeout=1)
gps = UbloxGps(port)

# Set up GPIO for LED using gpiozero
green_led = LED(17)  # Choose the appropriate GPIO pin connected to the green LED

def run():
    print("Listening for UBX Messages.")
    directory = '/home/dali/Documents/Rover-Tests-CSV'
    os.makedirs(directory, exist_ok=True)
    
    filename = datetime.now().strftime("%Y%m%d-%H%M%S") + '_coordinates.csv'
    filepath = os.path.join(directory, filename)
    
    try:
        with open(filepath, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Stream', 'Latitude', 'Longitude', 'DistFromEquator', 'DistFromPrimeMer'])
            while True:
                try:
                    coords = gps.geo_coords()
                    stream = gps.stream_nmea()
                    latitude = coords.lat
                    longitude = coords.lon
                    
                    lat_rad = math.radians(latitude)
                    lon_rad = math.radians(longitude)
                    
                    distFromEquator = 6371000 * lat_rad
                    distFromPrimeMer = 6371000 * math.cos(lat_rad) * lon_rad
                    
                    csvwriter.writerow([stream, latitude, longitude, distFromEquator, distFromPrimeMer])
                    print(f"Stream: {stream}, Latitude: {latitude}, Longitude: {longitude}, Equator: {distFromEquator}, Meridian: {distFromPrimeMer}")
                    
                    # Flash the green LED
                    green_led.on()
                    time.sleep(0.5)  # Adjust the duration as needed
                    green_led.off()

                except KeyError:
                    print("Coordinates not available")
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        port.close()

if __name__ == '__main__':
    time.sleep(30)
    run()
    pause()  # Keep the script running


