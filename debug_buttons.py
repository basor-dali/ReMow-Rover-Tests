import logging
from gpiozero import Button
from time import sleep

# GPIO pin numbers for the keypad
L1 = Button(5, pull_up=False)
L2 = Button(6, pull_up=False)
L3 = Button(13, pull_up=False)
L4 = Button(19, pull_up=False)

C1 = Button(12, pull_up=False)
C2 = Button(16, pull_up=False)
C3 = Button(20, pull_up=False)
C4 = Button(21, pull_up=False)

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_buttons():
    while True:
        logging.info(f"L1: {L1.is_pressed}, L2: {L2.is_pressed}, L3: {L3.is_pressed}, L4: {L4.is_pressed}")
        logging.info(f"C1: {C1.is_pressed}, C2: {C2.is_pressed}, C3: {C3.is_pressed}, C4: {C4.is_pressed}")
        sleep(1)

if __name__ == "__main__":
    try:
        debug_buttons()
    except KeyboardInterrupt:
        logging.info("\nDebugging stopped!")
