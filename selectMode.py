import RPi.GPIO as GPIO
import time

# GPIO pin numbers for the keypad
L1 = 5
L2 = 6
L3 = 13
L4 = 19

C1 = 12
C2 = 16
C3 = 20
C4 = 21

# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(L1, GPIO.OUT)
GPIO.setup(L2, GPIO.OUT)
GPIO.setup(L3, GPIO.OUT)
GPIO.setup(L4, GPIO.OUT)

GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Function to read a line of the keypad
def readLine(line, characters):
    GPIO.output(line, GPIO.HIGH)
    if(GPIO.input(C1) == 1):
        return characters[0]
    if(GPIO.input(C2) == 1):
        return characters[1]
    if(GPIO.input(C3) == 1):
        return characters[2]
    if(GPIO.input(C4) == 1):
        return characters[3]
    GPIO.output(line, GPIO.LOW)
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

# Main function
def main():
    print("Initializing Output Settings")
    DLAP = 0.0
    DRAP = 0.0
    print(f"Desired Left Actuator Position (DLAP) = {DLAP}, Send Output Command")
    print(f"Desired Right Actuator Position (DRAP) = {DRAP}, Send Output Command")
    print("De-Energize Electronic Blade Clutch Control Solenoid")

    while True:
        print("Waiting for user input...")
        mode = get_mode()
        print(f"User selected mode: {mode}")

        if mode == "1":  # STOP/END
            print("STOP/END mode selected")
            DLAP = 0.0
            DRAP = 0.0
            print(f"Desired Left Actuator Position (DLAP) = {DLAP}, Send Output Command")
            print(f"Desired Right Actuator Position (DRAP) = {DRAP}, Send Output Command")
            print("De-Energize Electronic Blade Clutch Control Solenoid")
        elif mode == "2":  # MOW MANUALLY
            print("MOW MANUALLY mode selected")
            print("Energize Electronic Blade Clutch Control Solenoid")
        elif mode == "3":  # RECORD
            print("RECORD mode selected")
            print("Enter 2-digit Mow ID:")
            mow_id = read_2_digit_combination()
            print(f"Mow ID: {mow_id}")
            print("Energize Electronic Blade Clutch Control Solenoid")
            # Additional logic for recording path
        elif mode == "A":  # RE-MOW
            print("RE-MOW mode selected")
            print("Enter 2-digit Mow ID:")
            mow_id = read_2_digit_combination()
            print(f"Mow ID: {mow_id}")
            # Additional logic for re-mowing
        else:
            print("Invalid mode selected")

        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication stopped!")
        GPIO.cleanup()