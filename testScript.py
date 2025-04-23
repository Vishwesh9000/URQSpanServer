import socket
import time
import random

HOST = '192.168.1.158'  # Same IP as in your listener
PORT = 55400            # Same port as in your listener

def send_measurements():
    # List of test messages (feel free to randomize or loop)
    
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            m = f"Measurement{random.randint(1,10)}: {random.randint(1,100)}"
            print(f"[SENDING]\t{m}")
            s.sendall(m.encode())
            time.sleep(.5)  # Send one message per second

if __name__ == "__main__":
    send_measurements()
