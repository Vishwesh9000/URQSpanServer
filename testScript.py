import socket
import time
import random

HOST = '192.168.56.1'  # Same IP as in your listener
PORT = 55400            # Same port as in your listener

def send_measurements():
    
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            m = f"Measurement{random.randint(1,8)}, {random.randint(1,100)}"
            print(f"[SENDING]\t{m}")
            s.sendall(m.encode())
            time.sleep(.5)  # Change interval

if __name__ == "__main__":
    send_measurements()
