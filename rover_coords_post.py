import serial
import json
from ublox_gps import UbloxGps
from time import time
import requests
import time
import configparser
import os

config = configparser.ConfigParser()
config_path = '/etc/thingsboard_config.ini'
config.read(config_path)
tb_url = config['ThingsBoard']['url']

# Initialize GPS and serial connection
port = serial.Serial('/dev/ttyAMA0', baudrate=38400, timeout=1)
gps = UbloxGps(port)

def run():
    print("Listening for UBX Messages.")
    try:
        while True:
            coords = gps.geo_coords()
            try:
                latitude = coords.lat
                longitude = coords.lon
                print(f"Latitude: {latitude}, Longitude: {longitude}")
                telemetry_with_ts = {"values": {"latitude": latitude, "longitude": longitude}}
                # Send POST request to the endpoint with telemetry data as JSON payload
                response = requests.post(tb_url, json=telemetry_with_ts)
                # Check the response status code
                if response.status_code == 200:
                    print("Telemetry data sent successfully!")
                else:
                    print("Failed to send telemetry data. Status code:", response.status_code)
                time.sleep(1)  # Send data every second
            except KeyError:
                print("Coordinates not available")
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        port.close()

if __name__ == '__main__':
    run()
