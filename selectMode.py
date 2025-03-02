import os
import subprocess
import logging
from time import strftime, sleep
import psutil
from gpiozero import LED, Button

# GPIO pin numbers for the keypad
L1 = Button(5)
L2 = Button(6)
L3 = Button(13)
L4 = Button(19)

C1 = Button(12, pull_up=False)
C2 = Button(16, pull_up=False)
C3 = Button(20, pull_up=False)
C4 = Button(21, pull_up=False)

# GPIO pin numbers for the LEDs
GREEN_LED = LED(17)
RED_LED = LED(27)

# Create the "Logs" directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), 'Logs')
os.makedirs(log_dir, exist_ok=True)

# Log file path with a unique name based on the current timestamp
log_file = os.path.join(log_dir, f'selectMode_{strftime("%Y%m%d-%H%M%S")}.log')

# Initialize logging with timestamp in every log message
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler for logging to a file
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Create a console handler for logging to the terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add both handlers to the root logger
logging.getLogger().addHandler(file_handler)
logging.getLogger().addHandler(console_handler)

# Function to read a line of the keypad
def readLine(line, characters):
    line_state = line.is_pressed  # Check if the line button is pressed
    if line_state:
        if C1.is_pressed:
            return characters[0]
        if C2.is_pressed:
            return characters[1]
        if C3.is_pressed:
            return characters[2]
        if C4.is_pressed:
            return characters[3]
    return None

# Function to determine the desired mode of operation
def get_mode():
    while True:
        mode = None
        mode = readLine(L1, ["1", "2", "3", "A"])
        if mode: return mode
        mode = readLine(L2, ["4", "5", "6", "B"])
        if mode: return mode
        mode = readLine(L3, ["7", "8", "9", "C"])
        if mode: return mode
        mode = readLine(L4, ["*", "0", "#", "D"])
        if mode: return mode
        sleep(0.1)

# Function to read a 2-digit combination
def read_2_digit_combination():
    digits = ""
    while len(digits) < 2:
        digit = get_mode()
        if digit.isdigit():
            digits += digit
            logging.info(f"Digit entered: {digit}")
    return digits

# Function to check if a Mow ID already exists
def check_mow_id(mow_id):
    for file in os.listdir("."):
        if file.endswith(".csv") and file.startswith(mow_id):
            return True
    return False

# Function to check if there is at least 10% free memory
def check_memory():
    memory = psutil.virtual_memory()
    free_memory_percentage = memory.available / memory.total * 100
    logging.info(f"Free memory: {free_memory_percentage:.2f}%")
    return free_memory_percentage >= 10

# Main function
def main():
    logging.info("Initializing Output Settings")
    DLAP = 0.0
    DRAP = 0.0
    logging.info(f"Desired Left Actuator Position (DLAP) = {DLAP}, Send Output Command")
    logging.info(f"Desired Right Actuator Position (DRAP) = {DRAP}, Send Output Command")
    logging.info("De-Energize Electronic Blade Clutch Control Solenoid")

    record_process = None

    while True:
        logging.info("Waiting for user input...")
        mode = get_mode()
        logging.info(f"User selected mode: {mode}")

        if mode == "A":  # RECORD
            logging.info("RECORD mode selected")
            while True:
                logging.info("Enter 2-digit Mow ID:")
                mow_id = read_2_digit_combination()
                if check_mow_id(mow_id):
                    logging.info("Mow ID already exists. Please enter a new Mow ID.")
                    RED_LED.on()  # Light up red LED
                    sleep(2)
                    RED_LED.off()  # Turn off red LED
                else:
                    if check_memory():
                        logging.info(f"Mow ID: {mow_id}")
                        GREEN_LED.on()  # Light up green LED
                        # Trigger recordDataToCsv.py with the Mow ID
                        record_process = subprocess.Popen(['python', 'recordDataToCsv.py', mow_id])
                        while True:
                            stop_mode = get_mode()
                            if stop_mode == "D":  # STOP
                                logging.info("STOP mode selected")
                                if record_process:
                                    record_process.terminate()  # Terminate the recordDataToCsv.py process
                                    record_process = None
                                logging.info("Desired Left Actuator Position (DLAP) = 0.0, Send Output Command")
                                logging.info("Desired Right Actuator Position (DRAP) = 0.0, Send Output Command")
                                logging.info("De-Energize Electronic Blade Clutch Control Solenoid")
                                GREEN_LED.off()  # Turn off green LED
                                break
                        break
                    else:
                        logging.info("Not enough free memory to start recording.")
                        RED_LED.on()  # Light up red LED
                        sleep(2)
                        RED_LED.off()  # Turn off red LED
                        break
        elif mode == "B":  # RE-MOW
            logging.info("RE-MOW mode selected")
            logging.info("Enter 2-digit Mow ID:")
            mow_id = read_2_digit_combination()
            logging.info(f"Mow ID: {mow_id}")
            # Additional logic for re-mowing
        elif mode == "C":  # MOW MANUALLY
            logging.info("MOW MANUALLY mode selected")
            logging.info("Energize Electronic Blade Clutch Control Solenoid")
        elif mode == "D":  # STOP
            logging.info("STOP mode selected")
            if record_process:
                record_process.terminate()  # Terminate the recordDataToCsv.py process
                record_process = None
            logging.info("Desired Left Actuator Position (DLAP) = 0.0, Send Output Command")
            logging.info("Desired Right Actuator Position (DRAP) = 0.0, Send Output Command")
            logging.info("De-Energize Electronic Blade Clutch Control Solenoid")
        else:
            logging.info("Invalid mode selected")

        sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("\nApplication stopped!")