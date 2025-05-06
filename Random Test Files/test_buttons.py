import logging
from gpiozero import Button, OutputDevice
from time import sleep, time

# GPIO pin numbers for the keypad
L1 = OutputDevice(5)
L2 = OutputDevice(6)
L3 = OutputDevice(13)
L4 = OutputDevice(19)

C1 = Button(12, pull_up=False, bounce_time=0.1)
C2 = Button(16, pull_up=False, bounce_time=0.1)
C3 = Button(20, pull_up=False, bounce_time=0.1)
C4 = Button(21, pull_up=False, bounce_time=0.1)

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

last_states = {
    'C1': False, 'C2': False, 'C3': False, 'C4': False
}
last_press_time = {
    'C1': 0, 'C2': 0, 'C3': 0, 'C4': 0
}
debounce_time = 0.5  # 500 milliseconds debounce time

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
            logging.info(characters[i])
            last_press_time[col] = current_time
        last_states[col] = state
    
    line.off()

def test_buttons():
    while True:
        read_line(L1, ["1", "2", "3", "A"])
        read_line(L2, ["4", "5", "6", "B"])
        read_line(L3, ["7", "8", "9", "C"])
        read_line(L4, ["*", "0", "#", "D"])
        sleep(0.1)

if __name__ == "__main__":
    try:
        test_buttons()
    except KeyboardInterrupt:
        logging.info("\nTest stopped!")
