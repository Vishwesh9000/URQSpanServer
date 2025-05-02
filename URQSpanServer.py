import socket, matplotlib.pyplot as plt, time, random, numpy as np, csv, sys, itertools
from matplotlib.widgets import Button
from multiprocessing import Process, Queue

graphDimensions = {"Line":(2,4), "Histogram":(2,4), "BoxPlot":(1,8)} #Rows and Columns of plots

expectedMeans = [None]*(graphDimensions["Line"][0]*graphDimensions["Line"][1]) #Expected mean for each graph
expectedMeans = [12, 20, 20, 25, 20, 10, 23, 5] #Change or comment out to disable expectedMean

tolerances = [.15] * (graphDimensions["Line"][0]*graphDimensions["Line"][1]) #points that are not inside mean+-tolerance will be marked with a red dot 
                                                            #(set to None to disable)

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
                print(f"[RECEIVED]\t\"{m}\"")
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
    fig = plt.figure()
    axs = []
    measurements = {}
    plt.ion()  # Enable interactive mode

    # Initialize Graph Cycler
    graphCycler = itertools.cycle(["Line", "Histogram", "BoxPlot"])
    graphType = next(graphCycler)
    
    def init_subplots(): #Creates the proper number of rows and columns of subplots based on graphType
        nonlocal fig, axs
        for ax in axs: ax.remove()
        axs = fig.subplots(*graphDimensions[graphType]) #shape and number of plots
        axs = axs.flatten()  
        for ax in axs:
            ax.ticklabel_format(useOffset=False)
        
        fig.subplots_adjust(
            left=0.04,   # space on the left side (0.0 - 1.0)
            right=.98,  # space on the right side (0.0 - 1.0)
            top=0.95,    # space at the top
            bottom=0.1, # space at the bottom
            wspace=0.3,  # width space between subplots
            hspace=0.4   # height space between subplots
        )

    init_subplots()
    plt.show(block=False)
    
    def cycleGraph(event):
        nonlocal graphType, graphCycler
        graphType = next(graphCycler)
        print(f"[BUTTON STATE] {graphType}")
        init_subplots() #Update graph rows and columns to match graphType

    ax_button = plt.axes([0.875, 0.01, 0.1, 0.05])
    button = Button(ax_button, 'Toggle Graph Type')
    button.on_clicked(cycleGraph)

    while True:
        while not q.empty():
            m = q.get()
            if m[0] not in measurements:
                measurements[m[0]] = [np.array([m[1]]), []]
                i = len(measurements)-1
                if tolerances[i] and expectedMeans[i] and abs(m[1]-expectedMeans[i]) > tolerances[i]:
                    measurements[m[0]][1].append(0)
            else:
                measurements[m[0]][0] = np.append(measurements[m[0]][0], m[1])

                i = list(measurements.keys()).index(m[0])
                if tolerances[i] and expectedMeans[i] and abs(m[1]-expectedMeans[i]) > tolerances[i]:
                    measurements[m[0]][1].append(measurements[m[0]][0].size-1)

        for i, (key, (val, outliers)) in enumerate(list(measurements.items())[:graphDimensions["Line"][0]*graphDimensions["Line"][1]]): #Limits measurements to number of plots
            axs[i].cla()
            axs[i].set_title(key)

            expectedMean = expectedMeans[i]
            tolerance = tolerances[i]

            mean = np.mean(val)
            stdDev = np.std(val)
            if expectedMean and tolerance:
                cpk = min(mean-(expectedMean-tolerance), expectedMean+tolerance-mean)/(3*stdDev)
            else:
                cpk = float('-inf')

            axs[i].tick_params(axis='y', labelsize=9)
            axs[i].tick_params(axis='x', labelsize=9)
            if graphType == "Line":
                fig.subplots_adjust(wspace=.2, hspace=.2)
                # Stat lines

                # Standard Deviation Lines
                for j in [-2,-1,1,2]:
                    axs[i].axhline(y=mean+j*stdDev, color='lightgray', linestyle=':',alpha=.5)

                axs[i].axhline(y=mean+3*stdDev, color='red', linestyle='--', alpha=.5)
                axs[i].axhline(y=mean-3*stdDev, color='red', linestyle='--',alpha=.5)

                # Mean Line
                axs[i].axhline(y=mean, color='black', linestyle='--',alpha=.5)

                if expectedMean:
                    # Expected Mean Line
                    axs[i].axhline(y=expectedMean, color='green', linestyle='--',alpha=.5)

                    if tolerance:
                        # Tolerance Lines
                        for j in [1, -1]:
                            axs[i].axhline(y=expectedMean+(tolerance*j), color='orange', linestyle='--',alpha=.5)

                # Graph lines
                axs[i].plot(range(1, val.size+1), val, color='blue')

                # Red dots for outliers
                for outlierIndex in outliers:
                    axs[i].plot(outlierIndex+1, val[outlierIndex], marker='.',color='red')

                # Statistical Parameters Text
                axs[i].text(
                    0.05, 0.95, f"μ={mean:.3f}\nσ={stdDev:.3f}\nCpk={cpk:.3f}",
                    transform=axs[i].transAxes,
                    verticalalignment='top',
                    fontsize=8,
                    bbox=dict(facecolor='white', alpha=0.5, edgecolor='gray')
                )

            elif graphType=="Histogram":
                fig.subplots_adjust(wspace=.15, hspace=.2)
                # Stat lines

                # Mean Line
                axs[i].axvline(x=mean, color='black', linestyle='--',alpha=.5)

                if expectedMean:
                    # Expected Mean Line
                    axs[i].axvline(x=expectedMean, color='green', linestyle='--',alpha=.5)

                    if tolerance:
                        # Tolerance Lines
                        for j in [1, -1]:
                            axs[i].axvline(x=expectedMean+(tolerance*j), color='orange', linestyle='--',alpha=.5)
                # Plot histogram
                numOfBins = 30
                if tolerance and expectedMean:
                    if expectedMean > np.max(val):
                        histMax = expectedMean
                    else:
                        histMax = max(np.max(val), expectedMean+tolerance)
                    if expectedMean < np.min(val):
                        histMin = expectedMean
                    else: histMin = min(np.min(val), expectedMean-tolerance)

                    binArray = np.linspace(histMin, histMax, numOfBins + 1)
                else:
                    binArray = np.linspace(np.min(val), np.max(val), numOfBins + 1)
                
                axs[i].hist(val, bins=binArray, edgecolor='black', linewidth=1)

                histMin -= (histMax-histMin)/20
                histMax += (histMax-histMin)/20

                axs[i].set_xlim(histMin, histMax)


            elif graphType=="BoxPlot":
                fig.subplots_adjust(wspace=.4)
                axs[i].tick_params(axis='x', which='both', bottom=False, labelbottom=False)
                if expectedMean:
                    # Expected Mean Line
                    axs[i].axhline(y=expectedMean, color='green', linestyle='--',alpha=.5)

                    if tolerance:
                        # Tolerance Lines
                        for j in [1, -1]:
                            axs[i].axhline(y=expectedMean+(tolerance*j), color='orange', linestyle='--',alpha=.5)

                # Plot Box Plot
                axs[i].boxplot(val, vert=True, showmeans=True)

                # Set y limits
                if expectedMean:
                    if expectedMean > np.max(val): boxMax = expectedMean
                    else: boxMax = max(np.max(val), expectedMean+(tolerance if tolerance else 0))
                else: boxMax = np.max(val)


                if expectedMean:
                    if expectedMean < np.min(val):boxMin = expectedMean
                    else: boxMin = min(np.min(val),expectedMean-(tolerance if tolerance else 0))
                else: boxMin = np.min(val)

                boxMin -= (boxMax-boxMin)/20
                boxMax += (boxMax-boxMin)/20
                axs[i].set_ylim(boxMin,boxMax)


            axs[i].relim()
            axs[i].autoscale_view()

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