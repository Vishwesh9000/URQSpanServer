import socket, matplotlib.pyplot as plt, time, random, numpy as np, csv, sys
from multiprocessing import Process, Queue

graphDimensions = (2,4) #Rows and Columns of plots
def listenForMeasurements(q):
    with open('measurements.csv', 'a', newline='') as file:
        file.write('\n\n\n')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((findIP(), 55400)) #Change to your IP
        sock.listen(1)
        print("[LISTENER READY]")
        while True:
            conn, addr = sock.accept()
            print(f"Connected by {addr}")
            while True:
                m = conn.recv(1024).decode()
                print(f"[RECEIVED]\t{m}")
                if not m: break
                elif "<UNITS>" in m: continue
                m ="".join([" "+i if i.isupper() else i for i in m]).split(",") #Decode camelcase
                m[1] = float(m[1])
                print(f"[RECEIVED]\t{m[0]}:\t{m[1]}")
                q.put(m)
                with open('measurements.csv', 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(m)
                    print("[SAVED]")
def plotData(q):
    measurements = {}
    plt.ion()  # Enable interactive mode

    fig, axs = plt.subplots(*graphDimensions) #shape and number of plots
    axs = axs.flatten()  
    plt.show(block=False)  

    while True:
        while not q.empty():
            m = q.get()
            if m[0] not in measurements:
                measurements[m[0]] = np.array([m[1]])
            else:
                measurements[m[0]] = np.append(measurements[m[0]], m[1])


        for i, (key, val) in enumerate(list(measurements.items())[:graphDimensions[0]*graphDimensions[1]]): #Limits measurements to number of plots
            axs[i].cla()
            axs[i].set_title(key)

            mean = np.mean(val)
            stdDev = np.std(val)

            axs[i].tick_params(axis='y', labelsize = 10)
            
            # plot lines
            for j in [-2,-1,1,2]:
                axs[i].axhline(y=mean+j*stdDev, color='lightgray', linestyle=':',alpha=.5)

            axs[i].axhline(y=mean+3*stdDev, color='red', linestyle='--', alpha=.5)
            axs[i].axhline(y=mean-3*stdDev, color='red', linestyle='--',alpha=.5)

            axs[i].axhline(y=mean, color='black', linestyle='--',alpha=.5)

            # Text
            axs[i].text(
                0.05, 0.95, f"μ={mean:.3f}\nσ={stdDev:.3f}",
                transform=axs[i].transAxes,
                verticalalignment='top',
                fontsize=8,
                bbox=dict(facecolor='white', alpha=0.5, edgecolor='gray')
            )

            axs[i].plot(range(1, val.size+1), val, color='blue')

            axs[i].set_title(key)
            
        fig.canvas.draw()          
        fig.canvas.flush_events()  

def findIP():
    ips = socket.gethostbyname_ex(socket.gethostname())[2]
    if len(ips) == 0:
        print("[ERROR] No IPs found")
        sys.exit()
    possibleIPs = [ip for ip in ips if ip.startswith("169.254.")]
    if len(possibleIPs) > 1:
        print(f"Pick IP number:")
        for i, ip in enumerate(possibleIPs):
            print(f"{i}:\t{ip}")
        try:
            num = int(input())
            return possibleIPs[num]
        except (ValueError, IndexError):
            print(f"[ERROR] {num} not valid ip number")
            print(f"Switching to first ip:\t{possibleIPs[0]}")
            return possibleIPs[0]
    elif len(possibleIPs) == 0:
        print("[WARNING] No ethernet connection found")
        print(f"[STATUS] Defaulting to WiFi IP: {ips[0]}")
        return ips[0]
    else:
        print(f"[STATUS] Using {possibleIPs[0]} as IP")
        return possibleIPs[0]
    
    


def fakeMeasurements(q):
    while True:
        
        sensor = f"Measurement {random.randint(1, 10)}"
        value = random.randint(0, 100)
        q.put([sensor, value])
        time.sleep(0.2) 
def main():
    q = Queue()
    proc = Process(target=listenForMeasurements, args=(q,), daemon=True)
    oproc = Process(target=fakeMeasurements, args=(q,), daemon=True)
    proc.start()
    # oproc.start()
    plotData(q)

if __name__ == "__main__":
    main()