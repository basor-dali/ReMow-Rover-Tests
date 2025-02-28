import RPi.GPIO as GPIO
import time
import os
import subprocess

# GPIO pin numbers for the keypad
L1 = 5
L2 = 6
L3 = 13
L4 = 19

C1 = 12
C2 = 16
C3 = 20
C4 = 21

# GPIO pin numbers for the LEDs
GREEN_LED = 17
RED_LED = 27

# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Setup GPIO pins for keypad rows as output
GPIO.setup(L1, GPIO.OUT)
GPIO.setup(L2, GPIO.OUT)
GPIO.setup(L3, GPIO.OUT)
GPIO.setup(L4, GPIO.OUT)

# Setup GPIO pins for keypad columns as input with pull-down resistors
GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Setup GPIO pins for LEDs as output
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)

# Function to read a line of the keypad
def readLine(line, characters):
    GPIO.output(line, GPIO.HIGH)  # Set the line to high
    if(GPIO.input(C1) == 1):
        return characters[0]
    if(GPIO.input(C2) == 1):
        return characters[1]
    if(GPIO.input(C3) == 1):
        return characters[2]
    if(GPIO.input(C4) == 1):
        return characters[3]
    GPIO.output(line, GPIO.LOW)  # Set the line back to low
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
        time.sleep(0.1)

# Function to read a 2-digit combination
def read_2_digit_combination():
    digits = ""
    while len(digits) < 2:
        digit = get_mode()
        if digit.isdigit():
            digits += digit
            print(f"Digit entered: {digit}")
    return digits

# Function to check if a Mow ID already exists
def check_mow_id(mow_id):
    for file in os.listdir("."):
        if file.endswith(".csv") and file.startswith(mow_id):
            return True
    return False

# Main function
def main():
    print("Initializing Output Settings")
    DLAP = 0.0
    DRAP = 0.0
    print(f"Desired Left Actuator Position (DLAP) = {DLAP}, Send Output Command")
    print(f"Desired Right Actuator Position (DRAP) = {DRAP}, Send Output Command")
    print("De-Energize Electronic Blade Clutch Control Solenoid")

    record_process = None

    while True:
        print("Waiting for user input...")
        mode = get_mode()
        print(f"User selected mode: {mode}")

        if mode == "A":  # RECORD
            print("RECORD mode selected")
            while True:
                print("Enter 2-digit Mow ID:")
                mow_id = read_2_digit_combination()
                if check_mow_id(mow_id):
                    print("Mow ID already exists. Please enter a new Mow ID.")
                    GPIO.output(RED_LED, GPIO.HIGH)  # Light up red LED
                    time.sleep(2)
                    GPIO.output(RED_LED, GPIO.LOW)  # Turn off red LED
                else:
                    print(f"Mow ID: {mow_id}")
                    GPIO.output(GREEN_LED, GPIO.HIGH)  # Light up green LED
                    # Trigger recordDataToCsv.py with the Mow ID
                    record_process = subprocess.Popen(['python', 'recordDataToCsv.py', mow_id])
                    break
        elif mode == "B":  # RE-MOW
            print("RE-MOW mode selected")
            print("Enter 2-digit Mow ID:")
            mow_id = read_2_digit_combination()
            print(f"Mow ID: {mow_id}")
            # Additional logic for re-mowing
        elif mode == "C":  # MOW MANUALLY
            print("MOW MANUALLY mode selected")
            print("Energize Electronic Blade Clutch Control Solenoid")
        elif mode == "D":  # STOP
            print("STOP mode selected")
            if record_process:
                record_process.terminate()  # Terminate the recordDataToCsv.py process
                record_process = None
            print("Desired Left Actuator Position (DLAP) = 0.0, Send Output Command")
            print("Desired Right Actuator Position (DRAP) = 0.0, Send Output Command")
            print("De-Energize Electronic Blade Clutch Control Solenoid")
        else:
            print("Invalid mode selected")

        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication stopped!")
        GPIO.cleanup()