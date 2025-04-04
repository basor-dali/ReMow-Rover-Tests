import os
import subprocess
import logging
from time import strftime, sleep, time
from gpiozero import LED, Button, OutputDevice
import gpiozero  # Import gpiozero to handle exceptions

# GPIO pin numbers for the keypad
L1 = OutputDevice(5)
L2 = OutputDevice(6)
L3 = OutputDevice(13)
L4 = OutputDevice(19)

C1 = Button(12, pull_up=False, bounce_time=0.1)
C2 = Button(16, pull_up=False, bounce_time=0.1)
C3 = Button(20, pull_up=False, bounce_time=0.1)
C4 = Button(21, pull_up=False, bounce_time=0.1)

# GPIO pin numbers for the LEDs
BLUE_LED = LED(22)
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

last_states = {
    'C1': False, 'C2': False, 'C3': False, 'C4': False
}
last_press_time = {
    'C1': 0, 'C2': 0, 'C3': 0, 'C4': 0
}
debounce_time = 0.5  # 500 milliseconds debounce time

# Function to read a line of the keypad
def read_line(line, characters):
    line.on()
    current_states = {
        'C1': C1.is_pressed,
        'C2': C2.is_pressed,
        'C3': C3.is_pressed,
        'C4': C4.is_pressed
    }
    
    current_time = time()
    for i, (col, state) in enumerate(current_states.items()):
        if state and not last_states[col] and (current_time - last_press_time[col] > debounce_time):
            last_press_time[col] = current_time
            line.off()
            return characters[i]
        last_states[col] = state
    
    line.off()
    return None

# Function to determine the desired mode of operation
def get_mode():
    while True:
        mode = read_line(L1, ["1", "2", "3", "A"])
        if mode: return mode
        mode = read_line(L2, ["4", "5", "6", "B"])
        if mode: return mode
        mode = read_line(L3, ["7", "8", "9", "C"])
        if mode: return mode
        mode = read_line(L4, ["*", "0", "#", "D"])
        if mode: return mode
        sleep(0.1)

# Function to monitor for 'D' press and kill the subprocess
def monitor_for_stop(process):
    while process.poll() is None:  # While the process is still running
        if read_line(L4, ["*", "0", "#", "D"]) == "D":
            logging.info("Mode D pressed, terminating the recording process")
            process.terminate()
        sleep(0.1)

def get_combination():
    combination = ""
    while len(combination) < 2:
        digit = read_line(L1, ["1", "2", "3", "A"]) or \
                read_line(L2, ["4", "5", "6", "B"]) or \
                read_line(L3, ["7", "8", "9", "C"]) or \
                read_line(L4, ["*", "0", "#", "D"])
        if digit and digit.isdigit():
            combination += digit
            logging.info(f"Digit entered: {digit}")
        else:
            # Flash BLUE LED while waiting for user input
            BLUE_LED.on()
            sleep(0.1)
            BLUE_LED.off()
            sleep(0.1)
    return combination

def validate_combination(combination):
    data_dir = os.path.join(os.path.dirname(__file__), 'Data')
    if not os.path.exists(data_dir):
        logging.info("Data directory does not exist")
        return False
    for filename in os.listdir(data_dir):
        if filename.startswith(combination):
            return True
    return False

def cleanup_gpio():
    try:
        BLUE_LED.off()
        RED_LED.off()
    except gpiozero.exc.GPIODeviceClosed:
        logging.warning("Attempted to turn off an already closed or uninitialized LED")
    finally:
        BLUE_LED.close()
        RED_LED.close()

def trigger_recording(combination):
    # script_path = os.path.join(os.path.dirname(__file__), 'recordDataToCsv.py')
    script_path = os.path.join(os.path.dirname(__file__), 'jeanClaude.py')
    logging.info(f"Triggering recording with combination: {combination}")
    logging.info(f"Running script: {script_path}")
    process = subprocess.Popen(['python3', script_path, combination], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    monitor_for_stop(process)
    stdout, stderr = process.communicate()
    logging.info(f"Subprocess output: {stdout}")
    logging.error(f"Subprocess error: {stderr}")

# Main function
def main():
    logging.info("Starting main function")
    while True:
        logging.info("Waiting for user input...")
        try:
            logging.debug("Turning on BLUE LED")
            if BLUE_LED.closed:
                logging.error("BLUE LED is closed or uninitialized")
            else:
                BLUE_LED.on()  # Light up blue LED while waiting for user input
        except gpiozero.exc.GPIODeviceClosed:
            logging.warning("Attempted to turn on an already closed or uninitialized LED")
        mode = get_mode()
        try:
            logging.debug("Flashing BLUE LED")
            for _ in range(5):  # Flash blue LED for 1 seconds (5 * 200ms)
                BLUE_LED.on()
                sleep(0.1)
                BLUE_LED.off()
                sleep(0.1)
        except gpiozero.exc.GPIODeviceClosed:
            logging.warning("Attempted to turn on/off an already closed or uninitialized LED")
        logging.info(f"User selected mode: {mode}")

        if mode == "A":
            logging.info("Mode A (RECORD) selected")
            logging.info("Enter a 2-digit combination")
            combination = get_combination()
            logging.info(f"Combination entered: {combination}")
            if validate_combination(combination):
                logging.info("File with the combination exists")
                try:
                    logging.debug("Turning on BLUE LED")
                    RED_LED.on()
                    sleep(5)
                    RED_LED.off()
                except gpiozero.exc.GPIODeviceClosed:
                    logging.warning("Attempted to turn on/off an already closed or uninitialized LED")
            else:
                logging.info("No file with the combination found")
                try:
                    logging.debug("Turning on BLUE LED")
                    for _ in range(5):  # Flash blue LED for 6 seconds (5 * 1100ms)
                        BLUE_LED.on()
                        sleep(1)
                        BLUE_LED.off()
                        sleep(.1)
                except gpiozero.exc.GPIODeviceClosed:
                    logging.warning("Attempted to turn on/off an already closed or uninitialized LED")
                trigger_recording(combination)
        elif mode == "B":
            logging.info("Mode B selected")
        elif mode == "C":
            logging.info("Mode C selected")
        elif mode == "D":
            logging.info("Mode D selected")
        else:
            logging.info("Invalid mode selected")

        sleep(1)

if __name__ == "__main__":
    try:
        logging.info("Application started")
        main()
    except KeyboardInterrupt:
        logging.info("\nApplication stopped!")
        cleanup_gpio()