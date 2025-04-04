import serial
import csv
import logging
import sys
import os
import time
import re
from time import strftime

def parse_nmea(sentence):
    if not sentence.startswith('$'):
        return None
    
    parts = sentence.split(',')
    message_type = parts[0]
    
    if message_type == '$GNGGA':
        try:
            time_str = parts[1]
            lat = float(parts[2]) if parts[2] else None
            lat_dir = parts[3]
            lon = float(parts[4]) if parts[4] else None
            lon_dir = parts[5]
            fix_quality = int(parts[6]) if parts[6] else None
            num_satellites = int(parts[7]) if parts[7] else None
            altitude = float(parts[9]) if parts[9] else None
            
            if lat and lon:
                lat_deg = int(lat / 100)
                lat_min = lat - (lat_deg * 100)
                lat = lat_deg + (lat_min / 60)
                if lat_dir == 'S':
                    lat = -lat
                
                lon_deg = int(lon / 100)
                lon_min = lon - (lon_deg * 100)
                lon = lon_deg + (lon_min / 60)
                if lon_dir == 'W':
                    lon = -lon
            
            return {
                'message_type': 'GGA',
                'time': time_str,
                'latitude': lat,
                'longitude': lon,
                'fix_quality': fix_quality,
                'num_satellites': num_satellites,
                'altitude': altitude
            }
        except (ValueError, IndexError) as e:
            logging.error(f"Error parsing GGA: {e}")
            return None
            
    elif message_type == '$GNRMC':
        try:
            time_str = parts[1]
            status = parts[2]
            lat = float(parts[3]) if parts[3] else None
            lat_dir = parts[4]
            lon = float(parts[5]) if parts[5] else None
            lon_dir = parts[6]
            speed_knots = float(parts[7]) if parts[7] else None
            course = float(parts[8]) if parts[8] else None
            
            speed_ms = speed_knots * 0.514444 if speed_knots is not None else None
            
            if lat and lon:
                lat_deg = int(lat / 100)
                lat_min = lat - (lat_deg * 100)
                lat = lat_deg + (lat_min / 60)
                if lat_dir == 'S':
                    lat = -lat
                
                lon_deg = int(lon / 100)
                lon_min = lon - (lon_deg * 100)
                lon = lon_deg + (lon_min / 60)
                if lon_dir == 'W':
                    lon = -lon
            
            return {
                'message_type': 'RMC',
                'time': time_str,
                'status': status,
                'latitude': lat,
                'longitude': lon,
                'speed': speed_ms,
                'course': course
            }
        except (ValueError, IndexError) as e:
            logging.error(f"Error parsing RMC: {e}")
            return None
    
    return None

def run(mow_id):
    logging.info("Starting NMEA parsing")
    
    data_dir = os.path.join(os.path.dirname(__file__), 'Data')
    os.makedirs(data_dir, exist_ok=True)
    
    filename = os.path.join(data_dir, f"{mow_id}_{strftime('%Y%m%d-%H%M%S')}_GPSData.csv")
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'latitude', 'longitude', 'speed', 'heading', 'altitude', 'fix_quality', 'satellites']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        with serial.Serial('/dev/ttyAMA0', baudrate=38400, timeout=1) as port:
            buffer = ""
            last_write_time = 0
            gps_data = {}
            
            while True:
                try:
                    data = port.read(port.in_waiting or 1).decode('ascii', errors='replace')
                    buffer += data
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        parsed = parse_nmea(line)
                        if parsed:
                            if parsed['message_type'] == 'GGA':
                                gps_data.update({
                                    'latitude': parsed['latitude'],
                                    'longitude': parsed['longitude'],
                                    'altitude': parsed['altitude'],
                                    'fix_quality': parsed['fix_quality'],
                                    'satellites': parsed['num_satellites']
                                })
                            elif parsed['message_type'] == 'RMC':
                                gps_data.update({
                                    'latitude': parsed['latitude'],
                                    'longitude': parsed['longitude'],
                                    'speed': parsed['speed'],
                                    'heading': parsed['course']
                                })
                    
                    current_time = time.time()
                    if current_time - last_write_time >= 1.0 and gps_data:
                        gps_data['timestamp'] = strftime("%Y-%m-%d %H:%M:%S")
                        writer.writerow(gps_data)
                        csvfile.flush()
                        logging.info(f"Data written to CSV: {gps_data}")
                        last_write_time = current_time
                        
                except KeyboardInterrupt:
                    logging.info("Program interrupted by user")
                    break
                except Exception as e:
                    logging.error(f"Unexpected error: {e}")
                    time.sleep(0.1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logging.error("Usage: python3 recordDataToCsv.py <combination>")
        sys.exit(1)
    combination = sys.argv[1]
    logging.info(f"Generated Mow ID: {combination}")
    run(combination)