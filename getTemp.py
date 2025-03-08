import os
import time

def get_cpu_temp():
    temp = os.popen("vcgencmd measure_temp").readline()
    return temp.replace("temp=", "").strip()

if __name__ == "__main__":
    try:
        while True:
            cpu_temp = get_cpu_temp()
            print(f"CPU Temperature: {cpu_temp}")
            time.sleep(5)  # Delay for 5 seconds
    except KeyboardInterrupt:
        print("Monitoring stopped.")