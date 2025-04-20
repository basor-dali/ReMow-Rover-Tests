import serial
import time

# Configure the serial port
serial_port = '/dev/ttyAMA0'  # Update to your port
baud_rate = 9600              # Initial baud rate to communicate with the module

ser = serial.Serial(serial_port, baud_rate, timeout=3)

def log_response(response):
    with open("response_log.txt", "a") as logfile:
        logfile.write(response.hex() + "\n")

def read_ack():
    """
    Reads and parses the UBX ACK/NACK response.
    Returns True if ACK is received, False if NACK is received, and None if no valid response.
    """
    response = ser.read(10)  # Read 10 bytes (typical ACK/NACK length)
    if len(response) < 10:
        print("Incomplete response received:", response.hex())
        log_response(response)
        return None
    if response[:2] == b'\xB5\x62':  # Check for UBX header
        cls_id = response[2]
        msg_id = response[3]
        if cls_id == 0x05:  # ACK/NACK class
            if msg_id == 0x01:  # ACK
                print("ACK received for the command.")
                return True
            elif msg_id == 0x00:  # NACK
                print("NACK received for the command.")
                return False
    print("Unexpected response:", response.hex())
    log_response(response)
    return None

def calculate_checksum(payload):
    """
    Calculates the UBX checksum for the given payload.
    """
    ck_a = 0
    ck_b = 0
    for byte in payload:
        ck_a = (ck_a + byte) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    return bytes([ck_a, ck_b])

def send_command(command):
    """
    Sends a UBX command to the module and waits for an ACK/NACK response.
    Retries up to 3 times if no valid response is received.
    """
    for _ in range(3):  # Retry up to 3 times
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(command)
        time.sleep(0.1)
        if read_ack():
            return True
    print("Command failed after 3 attempts.")
    return False

# Generation 9 Commands (UBX-CFG-VALSET)

# Command to set UART1 baud rate to 57600
# Key: CFG-UART1-BAUDRATE, Value: 57600 (0x0000E100)
payload = (
    b'\x06\x8A\x13\x00'  # UBX-CFG-VALSET header
    b'\x00'              # Version
    b'\x00\x00\x00'      # Layer (RAM)
    b'\x91\x60\x00\x00'  # Key ID: CFG-UART1-BAUDRATE
    b'\x00\xE1\x00\x00'  # Value: 57600 (0x0000E100)
    b'\x00\x00\x00\x00\x00'  # Padding
)
checksum = calculate_checksum(payload)
set_baud_rate_command = b'\xB5\x62' + payload + checksum
send_command(set_baud_rate_command)

# Command to set navigation rate to 1 Hz (1000 ms)
# Key: CFG-RATE-MEAS, Value: 1000 ms (0x03E8)
payload = (
    b'\x06\x8A\x13\x00'  # UBX-CFG-VALSET header
    b'\x00'              # Version
    b'\x00\x00\x00'      # Layer (RAM)
    b'\x1F\x30\x00\x00'  # Key ID: CFG-RATE-MEAS
    b'\xE8\x03\x00\x00'  # Value: 1000 ms (0x03E8)
    b'\x00\x00\x00\x00\x00'  # Padding
)
checksum = calculate_checksum(payload)
set_nav_rate_command = b'\xB5\x62' + payload + checksum
send_command(set_nav_rate_command)

# Command to enable NMEA GGA messages on UART1 at 1 Hz
# Key: CFG-MSGOUT-NMEA_GGA_UART1, Value: 1 (1 Hz)
payload = (
    b'\x06\x8A\x13\x00'  # UBX-CFG-VALSET header
    b'\x00'              # Version
    b'\x00\x00\x00'      # Layer (RAM)
    b'\x91\x20\x00\x00'  # Key ID: CFG-MSGOUT-NMEA_GGA_UART1
    b'\x01\x00\x00\x00'  # Value: 1 (1 Hz)
    b'\x00\x00\x00\x00\x00'  # Padding
)
checksum = calculate_checksum(payload)
enable_gga_command = b'\xB5\x62' + payload + checksum
send_command(enable_gga_command)

ser.close()

# Inform the user to reconnect at the new baud rate
print("Configuration complete. Reconnect at 57600 baud.")