#!/usr/bin/env python
# ----- Import -----
# Module GUI
import tkinter as tk
from tkinter import ttk
from multiprocessing import Queue
from multiprocessing import Process

# TCP Module
import socket

# Module Plot
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
#from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np

# Module Multi-Threading
import time

# Module Python GPIO
#import RPi.GPIO as GPIO

# ----- Global Variables -----
# --- Styling ---
# Fonts
LARGE_FONT = ("Times", 20)
NORM_FONT = ("Times", 10)
SMALL_FONT = ("Times", 8)

# General Style
style.use("ggplot")

# Color Pallate
darkColor = "#183A54"
lightColor = "#00A3E0"

# Time Display Format
time_format = "%H:%M:%S"

# Graph Markers
num_markers = 5

# --- Window Settings ---
# Window Size
application_size = "1200x600"

# --- Graph Frame ---
figureFrame = plt.figure()
#a = f.add_subplot(111)

# --- Defaults ---
global graph
programName = "pt"
force_update_counter = 9000
Indicator = "None"
sampleSize = 10000

# --- Labels ---
fsmptlabels = ["FSM: PT1", "FSM: PT2", "FSM: PT3", "FSM: PT4", "FSM: PT5", "FSM: PT6", "FSM: PT7", "FSM: PT8", "FSM: PT9"]
gsmptlabels = ["GSM: PT1", "", "", "", "", "", "", ""]
fsmtclabels = ["FSM: TC1", "FSM: TC2", "FSM: TC3", "FSM: TC4", "FSM: TC5", "FSM: TC6", "FSM: TC7", "FSM: TC8", "FSM: TC9"]
gsmtclabels = ["GSM: TC1", "GSM: TC2", "GSM: TC3", "GSM: TC4", "GSM: TC5", "GSM: TC6", "GSM: TC7", "GSM: TC8", "GSM: TC9"]

# --- Colors ---
fsmptcolors = ['b', 'g', 'r']
gsmptcolors = ['c', 'm', 'k']
fsmtccolors = ['b', 'g', 'r']
gsmtccolors = ['c', 'm', 'k', 'y', '0.5', '#ff66cc', '#663300']

# ----- Global Function Definitions -----

# Reads queue and returns list in format [[time, reltime, sensor1, ...], [time, reltime, sensor1, ...], ...]
def sortlist(q):
    data = q.get()
    datalist = data.split('\n')
    datalist.pop()
    datalist = [i.split(',') for i in datalist]
    for i in range (0, len(datalist[0])):
        if datalist[0][i] == "tc1":
            position = i
            break
    datalist.pop(0)
    datalist.append([position])
    return datalist

# Gets list in format [[time, reltime, sensor1, ...], [time, reltime, sensor1, ...], ...] to [[time], [reltime], [sensor1], ...]
def organizelist(datalist):
    organizedlist = []
    for i in range (0, len(datalist[0])):
        temp = []
        for j in range (0, len(datalist)):
            temp.append(datalist[j][i])
        organizedlist.append(temp)
    return organizedlist

# Gets a list of time, PT data, and TC data, and returns a list of time with PT data
def getpressure(datalist, position):
    pressurelist = []
    for i in datalist:
        temp = []
        for j in range (0, position):
            temp.append(i[j])
        pressurelist.append(temp)
    #print (pressurelist)
    return organizelist(pressurelist)

# Gets a list of time, PT data, and TC data, and returns a list of time with TC data
def getthermo(datalist, position):
    thermolist = []
    #print (datalist)
    for i in datalist:
        temp = []
        temp.append(i[0])
        temp.append(i[1])
        for j in range (position, len(i)):
            temp.append(i[j])
        thermolist.append(temp)
    return organizelist(thermolist)

def animate(i, FSMq, GSMq):
    global refreshRate
    global force_update_counter


    if not FSMq.empty() and not GSMq.empty():
        fsmdatalist = sortlist(FSMq)
        fsmposition = fsmdatalist[len(fsmdatalist) - 1][0]
        fsmdatalist.pop(len(fsmdatalist) - 1)
        fsmpressurelist = getpressure(fsmdatalist, fsmposition)
        fsmthermolist = getthermo(fsmdatalist, fsmposition)
        gsmdatalist = sortlist(GSMq)
        gsmposition = gsmdatalist[len(gsmdatalist) - 1][0]
        gsmdatalist.pop(len(gsmdatalist) - 1)
        gsmpressurelist = getpressure(gsmdatalist, gsmposition)
        gsmthermolist = getthermo(gsmdatalist, gsmposition)
        drawgraph = True
    else:
        drawgraph = False

    try:
        if graph == "Pressure Transducer":

            # Run through the pressure lists and plot them on the graph
            if drawgraph:
                gridgraph = plt.subplot2grid((6, 4), (0, 0), rowspan=5, colspan=4)
                gridgraph.clear()
                for i in range (2, 3):
                    gridgraph.plot(np.array([float(j) for j in gsmpressurelist[0]]), np.array([float(j) for j in gsmpressurelist[i]]), gsmptcolors[i-2], label = gsmptlabels[i-2])
           #     for i in range (2, 2):
           #         gridgraph.plot(np.array([float(j) for j in fsmpressurelist[0]]), np.array([float(j) for j in fsmpressurelist[i]]), fsmptcolors[i-2], label = fsmptlabels[i-2])
                gridgraph.xaxis.set_major_locator(mticker.MaxNLocator(num_markers))
                gridgraph.legend(bbox_to_anchor=(0, -0.375, 0, 0), loc=3, ncol=3, borderaxespad=0)
                gridgraph.set_title("Pressure Transducer")

        if graph == "Thermocouple":
            # Run through the thermo lists and plot them on the graph
            if drawgraph:
                gridgraph = plt.subplot2grid((6, 4), (0, 0), rowspan=5, colspan=4)
                gridgraph.clear()
                for i in range (2, len(gsmthermolist)):
                    gridgraph.plot(np.array([float(j) for j in gsmthermolist[0]]), np.array([int(j) for j in gsmthermolist[i]]), gsmtccolors[i-2], label = gsmtclabels[i-2])
                for i in range (2, len(fsmthermolist)):
                    gridgraph.plot(np.array([float(j) for j in fsmthermolist[0]]), np.array([int(j) for j in fsmthermolist[i]]), fsmtccolors[i-2], label = fsmtclabels[i-2])
                gridgraph.xaxis.set_major_locator(mticker.MaxNLocator(num_markers))
                gridgraph.legend(bbox_to_anchor=(0, -0.375, 0, 0), loc=3, ncol=3, borderaxespad=0)
                gridgraph.set_title("Thermocouple")

        if graph == "Load Cell":
            # Run through the thermo lists and plot them on the graph

            if plotgraph:
                graphgrid = plt.subplot2grid((6, 4), (0, 0), rowspan=5, colspan=4)
                graphgrid.clear()
                graphgrid.xaxis.set_major_locator(mticker.MaxNLocator(num_markers))
                graphgrid.set_title("Load Cell")

    except Exception as e:
        print("Failure due to: ", e)

# Popup Message Function
def popupmsg(msg):
    popup = tk.Tk()

    popup.wm_title("Warning!")
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)

    button1 = ttk.Button(popup, text="Okay", command=popup.destroy)
    button1.pack()
    popup.mainloop()

# Switch Displayed Graphs
def changeGraph(changevalue):
    global graph
    graph = changevalue

# Change graph sizes
def changeDataSize(ds):
    global sampleSize
    global force_update_counter

    # Too Much Data Popup
    # -- To Implement --

    sampleSize = ds
    force_update_counter = 9000

# Add Warning Indicators from instrumentation
def addIndicator(option):
    global Indicator
    global force_update_counter

    if (option == "Alarm"):
        print("Alarm is On")

    Indicator = option
    force_update_counter = 9000

# Send commands to launch pad
def setCommand(command_out):
    print(command_out)
    popupmsg(command_out)

# Define basic GUI initialization
class CtrlBox(tk.Tk):

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    # Default Code for Creating a Window
    def __init__(self, *args, **kwargs):

        global graph
        graph = "Pressure Transducer"
        tk.Tk.__init__(self, *args, **kwargs)

        # GUI
        tk.Tk.wm_title(self, "Control Box")

        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # ----- Menu -----
        menubar = tk.Menu(container)

        # --- File Menu ---
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Settings", command=lambda: popupmsg("NA"))
        file_menu.add_command(label="Save Settings", command=lambda: popupmsg("Not Support Yet!"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # --- Graph Menu ---
        graphChoice = tk.Menu(menubar, tearoff=1)
        graphChoice.add_command(label="Pressure Transducer", command=lambda: changeGraph("Pressure Transducer"))
        graphChoice.add_command(label="Thermocouple", command=lambda: changeGraph("Thermocouple"))
        graphChoice.add_command(label="Load Cell", command=lambda: changeGraph("Load Cell"))
        menubar.add_cascade(label="Graph", menu=graphChoice)

        # --- TimeFrame Menu ---
        dataTF = tk.Menu(menubar, tearoff=1)
        dataTF.add_command(label="Size 1000", command=lambda: changeDataSize(1000))
        dataTF.add_command(label="Size 5000", command=lambda: changeDataSize(5000))
        dataTF.add_command(label="Size 10000", command=lambda: changeDataSize(10000))
        menubar.add_cascade(label="Data", menu=dataTF)

        # --- Indicator Menu ---
        indicator = tk.Menu(menubar, tearoff=1)
        indicator.add_command(label="None", command=lambda: addIndicator("None"))
        indicator.add_command(label="Alarm", command=lambda: addIndicator("Alarm"))
        menubar.add_cascade(label="Indicator", menu=indicator)

        # --- Command Menu ---
        command_menu = tk.Menu(menubar, tearoff=1)
        command_menu.add_command(label="Solenoid Valves 1", command=lambda: setCommand("Valve 1"))
        command_menu.add_command(label="Solenoid Valves 2", command=lambda: setCommand("Valve 2"))
        command_menu.add_command(label="Solenoid Valves 3", command=lambda: setCommand("Valve 3"))
        command_menu.add_command(label="Solenoid Valves 4", command=lambda: setCommand("Valve 4"))
        command_menu.add_command(label="Solenoid Valves 5", command=lambda: setCommand("Valve 5"))
        command_menu.add_separator()
        command_menu.add_command(label="Ignition", command=lambda: setCommand("burnbabyburn"))
        command_menu.add_separator()
        command_menu.add_command(label="Automated Launch", command=lambda: setCommand("Launch Sequence"))
        command_menu.add_separator()
        command_menu.add_command(label="Abort", command=lambda: setCommand("Houston, We Have a Problem"))
        menubar.add_cascade(label="Command", menu=command_menu)

        # --- Help Menu ---
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help", command=lambda: popupmsg("Help"))
        help_menu.add_separator()
        help_menu.add_command(label="About", command=lambda: popupmsg("About"))
        menubar.add_cascade(label="Help", menu=help_menu)

        # Loading Menu Bar
        tk.Tk.config(self, menu=menubar)

        # ----- Application Windows -----
        self.frames = {}
        frame = BTCe_Page(container, self)
        self.frames[BTCe_Page] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(BTCe_Page)

# Test Page 5
class BTCe_Page(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.columnconfigure(0, weight=11)
        self.columnconfigure(1, weight=1)

        subFrame1 = tk.Frame(self)
        subFrame1.grid(row=2, column=0, sticky="nsew")

        subFrame1.columnconfigure(0, weight=11)
        subFrame1.columnconfigure(1, weight=1)

        sub2Frame1 = tk.Frame(subFrame1)
        sub2Frame1.grid(row=0, column=0, sticky="nsew")

        canvas = FigureCanvasTkAgg(figureFrame, master=sub2Frame1)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, sub2Frame1)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        sub2Frame2 = tk.Frame(subFrame1)
        sub2Frame2.grid(row=0, column=1, sticky="nsew")

        vbar = tk.Scrollbar(sub2Frame2, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        canvas.get_tk_widget().config(yscrollcommand=vbar.set)

        vbar.config(command=canvas.get_tk_widget().yview)

        subFrame2 = tk.Frame(self)
        subFrame2.grid(row=2, column=1, sticky="n")


# Main Run Functions


def drawgraph(FSMq, GSMq):
    root = CtrlBox()
    root.geometry(application_size)
    ani = animation.FuncAnimation(figureFrame, animate, fargs = (FSMq, GSMq), interval=100)
    root.mainloop()

def TCPClient(FSMq, GSMq):
    FSMHOST, FSMPORT = "192.168.1.112", 5557
    GSMHOST, GSMPORT = "192.168.1.112", 5555
    # Create a socket (SOCK_STREAM means a TCP socket)

    response = "Data Received"
    response = response.encode('utf-8')

    while True:
        FSM = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        FSM.connect((FSMHOST, FSMPORT))
        FSM.sendall(response)
        FSMdata = FSM.recv(16384).decode('utf-8')
        FSM.close()
        GSM = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        GSM.connect((GSMHOST, GSMPORT))
        GSM.sendall(response)
        GSMdata = GSM.recv(16384).decode('utf-8')
        GSM.close()
        FSMq.put(FSMdata)
        GSMq.put(GSMdata)


if __name__ == '__main__':
    FSMq = Queue()
    GSMq = Queue()
    STATUSq = Queue()
    p1 = Process(target = TCPClient, args = (FSMq, GSMq,))
    p2 = Process(target = drawgraph, args = (FSMq, GSMq,))
    p1.start()
    p2.start()
