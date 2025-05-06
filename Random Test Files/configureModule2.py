import serial
import time

def send_cfg_rate_command(port='/dev/ttyAMA0', baudrate=9600):
    sync_chars = b'\xB5\x62'
    msg_class = b'\x06'
    msg_id = b'\x08'
    payload_length = b'\x06\x00'
    payload = b'\xF4\x01' + b'\x01\x00' + b'\x00\x00'
    
    chk_data = msg_class + msg_id + payload_length + payload
    ck_a = 0
    ck_b = 0
    for byte in chk_data:
        ck_a = (ck_a + byte) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    checksum = bytes([ck_a, ck_b])
    
    ubx_command = sync_chars + chk_data + checksum
    print("Sending UBX command (hex):")
    print(ubx_command.hex(' '))
    
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        time.sleep(2)  # Allow the connection to settle
        
        # Clear any previous data in the input buffer
        ser.reset_input_buffer()
        
        ser.write(ubx_command)
        print("Command sent!")
        
        time.sleep(0.5)
        response = ser.read_all()
        if response:
            print("Response (hex):")
            print(response.hex(' '))
        else:
            print("No response received.")
        
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    send_cfg_rate_command(port='/dev/ttyAMA0', baudrate=9600)