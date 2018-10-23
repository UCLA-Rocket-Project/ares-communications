from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import numpy as np
import pyqtgraph
import socket
import time

GSMHOST, GSMPORT = '192.168.1.99', 5555
FSMHOST, FSMPORT = '192.168.1.99', 5557

#gsmptlabels = ["GSM: PT1" , "GSM: PT2", "GSM: PT3", "GSM: PT4", "GSM: PT5", "GSM: PT6", "GSM: PT7", "GSM: PT8", "GSM: PT9"]
GSM_PT_LABELS = ["PresTank " , "OxTank", "FuelTank "]
#fsmptlabels = ["FSM: PT1", "FSM: PT2", "FSM: PT3", "FSM: PT4", "FSM: PT5", "FSM: PT6", "FSM: PT7", "FSM: PT8", "FSM: PT9"]
FSM_PT_LABELS = ["FuelManifold", "OxManifold", "Combustion Chamber"]
#gsmtclabels = ["GSM: TC1", "GSM: TC2", "GSM: TC3", "GSM: TC4", "GSM: TC5", "GSM: TC6", "GSM: TC7", "GSM: TC8", "GSM: TC9"]
GSM_TC_LABELS = ["GSM: TC1", "CCCenter", "Lower1/4Ox", "OxVent", "Middle1/4Ox", "Top1/4Ox", "GSM: TC7"]
#fsmtclabels = ["FSM: TC1", "FSM: TC2", "FSM: TC3", "FSM: TC4", "FSM: TC5", "FSM: TC6", "FSM: TC7", "FSM: TC8", "FSM: TC9"]
FSM_TC_LABELS = ["FSM: TC1", "Ambient", "FSM: TC3"]
GSM_LC_LABELS = []
FSM_LC_LABELS = []

# Offsets and Scales - has to have 3 values
FSM_PT_OFFSET = [0, 0, 0, 0, 0]
FSM_PT_SCALE = [0.9754, 0.9754, 0.9754, 1, 1]
GSM_PT_OFFSET = [-56.9524, 0, 0, 0, 0]
GSM_PT_SCALE = [0.91383, 0.9731, 0.9731, 1, 1]

class ProcessGraph(QtCore.QThread):
	def __init__(self, GraphWindow, parent=None):
		super(ProcessGraph, self).__init__(parent)
		self.graph_window = GraphWindow
	
	def run(self):
		while True:
			self.TCPClient()
			if self.graph_window.graph_ready == False:
				self.setnpdata()

	# Create a socket (SOCK_STREAM means a TCP socket)
	def TCPClient(self):
		response = "1"
		response = response.encode('utf-8')
		if self.graph_window.gsm_state == True:
			try:
				GSM = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				GSM.connect((GSMHOST, GSMPORT))
				GSM.sendall(response)
				GSMdata = GSM.recv(16384).decode('utf-8')
				GSM.close()
				self.sortdata(GSMdata, "GSM")
				self.graph_window.gsm_state = True
			except socket.error:
				print ("GSM Error")
				self.graph_window.gsm_state = False
				self.graph_window.gui_update = True

		if self.graph_window.fsm_state == True:
			try:
				FSM = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				FSM.connect((FSMHOST, FSMPORT))
				FSM.sendall(response)
				FSMdata = FSM.recv(16384).decode('utf-8')
				FSM.close()
				self.sortdata(FSMdata, "FSM")
				self.graph_window.fsm_state = True
			except socket.error:
				print ("FSM Error")
				self.graph_window.fsm_state = False
				self.graph_window.gui_update = True

	def sortdata(self, data, type):

		temp_abstime = []
		temp_reltime = []
		temp_pt = []
		temp_tc = []
		temp_lc = []

		data = data.split('\n')
		data = [i.split(',') for i in data]
		data.pop()
		
		if (type == "GSM"):
			self.graph_window.gsm_labels = data.pop(0)
			label_list = self.graph_window.gsm_labels
			length = len(self.graph_window.gsm_labels)
		elif (type == "FSM"):
			self.graph_window.fsm_labels = data.pop(0)
			label_list = self.graph_window.fsm_labels
			length = len(self.graph_window.fsm_labels)
		else:
			length = 0

		for i in range (0, length):
			temp_list = []
			for j in data:
				temp_list.append(j[i])

			if ("abs" in label_list[i]):
				temp_abstime = temp_list
			elif ("rel" in label_list[i]):
				temp_reltime = temp_list
			elif ("pt" in label_list[i]):
				temp_pt.append(temp_list)
			elif ("tc" in label_list[i]):
				temp_tc.append(temp_list)
			elif ("lc" in label_list[i]):
				temp_lc.append(temp_list)
			else:
				pass

		if (type == "GSM"):
			self.graph_window.gsm_abstime = list([float(i) for i in temp_abstime])
			self.graph_window.gsm_reltime = list([float(i) for i in temp_reltime])
			self.graph_window.gsm_pt = [self.calibrate(i, GSM_PT_SCALE, GSM_PT_OFFSET) for i in temp_pt]
			self.graph_window.gsm_tc = [[int(j) for j in i] for i in temp_tc]
			self.graph_window.gsm_lc = [[int(j) for j in i] for i in temp_lc]
		elif (type == "FSM"):
			self.graph_window.fsm_abstime = list([float(i) for i in temp_abstime])
			self.graph_window.fsm_reltime = list([float(i) for i in temp_abstime])
			self.graph_window.fsm_pt = [self.calibrate(i, FSM_PT_SCALE, FSM_PT_OFFSET) for i in temp_pt]
			self.graph_window.fsm_tc = [[int(j) for j in i] for i in temp_tc]
			self.graph_window.fsm_lc = [[int(j) for j in i] for i in temp_lc]
		else:
			pass

	def calibrate(self, sensor_data, scale, offset):
		temp = []
		for i in range (0, len(sensor_data)):
			temp.append((float(sensor_data[i]) * scale[1]) + offset[1])
		return temp

	def setnpdata(self):
		if self.graph_window.graph_type == 1:
			self.graph_window.graph_gsm_labels = GSM_PT_LABELS
			self.graph_window.graph_gsm_time = np.array(self.graph_window.gsm_abstime)
			self.graph_window.graph_gsm_sensor = [np.array(i) for i in self.graph_window.gsm_pt]
			self.graph_window.graph_fsm_labels = FSM_PT_LABELS
			self.graph_window.graph_fsm_time = np.array(self.graph_window.fsm_abstime)
			self.graph_window.graph_fsm_sensor = [np.array(i) for i in self.graph_window.fsm_pt]
		elif self.graph_window.graph_type == 2:
			self.graph_window.graph_gsm_labels = GSM_TC_LABELS
			self.graph_window.graph_gsm_time = np.array(self.graph_window.gsm_abstime)
			self.graph_window.graph_gsm_sensor = [np.array(i) for i in self.graph_window.gsm_tc]
			self.graph_window.graph_fsm_labels = FSM_TC_LABELS
			self.graph_window.graph_fsm_time = np.array(self.graph_window.fsm_abstime)
			self.graph_window.graph_fsm_sensor = [np.array(i) for i in self.graph_window.fsm_tc]
		elif self.graph_window.graph_type == 3:
			self.graph_window.graph_gsm_labels = GSM_LC_LABELS
			self.graph_window.graph_gsm_time = np.array(self.graph_window.gsm_abstime)
			self.graph_window.graph_gsm_sensor = [np.array(i) for i in self.graph_window.gsm_lc]
			self.graph_window.graph_fsm_labels = FSM_LC_LABELS
			self.graph_window.graph_fsm_time = np.array(self.graph_window.fsm_abstime)
			self.graph_window.graph_fsm_sensor = [np.array(i) for i in self.graph_window.fsm_lc]
		self.graph_window.graph_ready = True

class GraphWindow(QtWidgets.QMainWindow):

	def __init__(self, parent=None):
		super(GraphWindow, self).__init__(parent)
		self.setWindowTitle('ARES')

		# Set up pyqtgraph
		self.left_axis_labels = ["Pressure", "Temperature", "Force"]
		self.left_axis_units = ["psi", "°C", "lbf"]
		self.bottom_axis_label = "Absolute Time (s)"
		self.window = pyqtgraph.GraphicsWindow()
		self.window.setBackground('w')
		self.sensorplot = self.window.addPlot(title='Pressure Transducer')
		self.sensorplot.showGrid(x=True, y=True, alpha=0.5)
		self.sensorplot.setLabel('left', text=self.left_axis_labels[0], units=self.left_axis_units[0])
		self.sensorplot.setLabel('bottom', text=self.bottom_axis_label)
		self.setCentralWidget(self.window)
		self.viewbox = self.window.addViewBox()
		self.legend = pyqtgraph.LegendItem()
		self.legend.setParentItem(self.viewbox)
		self.legend.anchor((0,0), (0,0))
		self.statusbar = self.statusBar()

		# Set up variables for data
		self.graph_type = 1
		self.gsm_state = True
		self.gsm_labels = []
		self.gsm_abstime = []
		self.gsm_reltime = []
		self.gsm_pt = []
		self.gsm_tc = []
		self.gsm_lc = []
		self.fsm_state = True
		self.fsm_labels = []
		self.fsm_abstime = []
		self.fsm_reltime = []
		self.fsm_pt = []
		self.fsm_tc = []
		self.fsm_lc = []
		self.filter_list = []
		self.graph_ready = True
		self.get_new_data = True

		# Set up variables for graphing
		self.graph_gsm_labels = []
		self.graph_gsm_time = np.array([])
		self.graph_gsm_sensor = []
		self.graph_fsm_labels = []
		self.graph_fsm_time = np.array([])
		self.graph_fsm_sensor = []

		# Set up GUI
		self.windows = [PopUpWindow(self, i) for i in range(1, 4)]
		self.filter_tabs = []
		self.menubar = self.menuBar()
		self.MenuBar(GSM_PT_LABELS, FSM_PT_LABELS)
		self.gui_update = False
		self.statusbar_message = ""

		# Update the graph
		self.update = ProcessGraph(self)
		self.update.start()

		# Update the graph
		self.timer = QtCore.QTimer(self)
		self.timer.setInterval(0) # in milliseconds
		self.timer.start()
		self.timer.timeout.connect(self.refresh)

	def MenuBar(self, gsm_label, fsm_label):
		# create an instance of menu bar
		self.menubar.clear()
		self.filter_tabs.clear()

		# add menubar items
		file_menu = self.menubar.addMenu('File')
		graph_menu = self.menubar.addMenu('Graph')
		view_menu = self.menubar.addMenu('View')
		filter_menu = self.menubar.addMenu('Filter')

		# add dropdown menus
		exit_action = QtGui.QAction('Exit', self)
		exit_action.triggered.connect(self.close)
		file_menu.addAction(exit_action)

		pt_action = QtGui.QAction("Pressure Transducer", self)
		pt_action.triggered.connect(lambda checked, index=1: self.changegraph(index))
		graph_menu.addAction(pt_action)
		tc_action = QtGui.QAction("Thermocouple", self)
		tc_action.triggered.connect(lambda checked, index=2: self.changegraph(index))
		graph_menu.addAction(tc_action)
		lc_action = QtGui.QAction("Load Cell", self)
		lc_action.triggered.connect(lambda checked, index=3: self.changegraph(index))
		graph_menu.addAction(lc_action)

		ptwindow_action = QtGui.QAction("PT Values", self)
		ptwindow_action.triggered.connect(lambda checked, index=0: self.showwindow(index))
		view_menu.addAction(ptwindow_action)
		tcwindow_action = QtGui.QAction("TC Values", self)
		tcwindow_action.triggered.connect(lambda checked, index=1: self.showwindow(index))
		view_menu.addAction(tcwindow_action)
		lcwindow_action = QtGui.QAction("LC Values", self)
		lcwindow_action.triggered.connect(lambda checked, index=2: self.showwindow(index))
		view_menu.addAction(lcwindow_action)

		if (self.gsm_state == True):
			for index in range(0, len(gsm_label)):
				filter_action = QtGui.QAction(gsm_label[index], self, checkable=True)
				filter_action.setChecked(not gsm_label[index] in self.filter_list)
				filter_action.triggered.connect(lambda checked, index=index: self.gsm_filtergraph(index))
				self.filter_tabs.append(filter_action)

		if (self.fsm_state == True):
			for index in range(0, len(fsm_label)):
				filter_action = QtGui.QAction(fsm_label[index], self, checkable=True)
				filter_action.setChecked(not fsm_label[index] in self.filter_list)
				filter_action.triggered.connect(lambda checked, index=index: self.fsm_filtergraph(index))
				self.filter_tabs.append(filter_action)

		for filter_item in self.filter_tabs:
			filter_menu.addAction(filter_item)

	def changegraph(self, index):
		self.graph_type = index

		if (self.graph_type == 1):
			self.sensorplot.setTitle("Pressure Transducer")
			self.MenuBar(GSM_PT_LABELS, FSM_PT_LABELS)
			self.sensorplot.setLabel('left', text=self.left_axis_labels[index - 1], units=self.left_axis_units[index - 1])
			self.sensorplot.setLabel('bottom', text=self.bottom_axis_label)
		elif (self.graph_type == 2):
			self.sensorplot.setTitle("Thermocouple")
			self.MenuBar(GSM_TC_LABELS, FSM_TC_LABELS)
			self.sensorplot.setLabel('left', text=self.left_axis_labels[index - 1], units=self.left_axis_units[index - 1])
			self.sensorplot.setLabel('bottom', text=self.bottom_axis_label)
		elif (self.graph_type == 3):
			self.sensorplot.setTitle("Load Cell")
			self.MenuBar(GSM_LC_LABELS, FSM_LC_LABELS)
			self.sensorplot.setLabel('left', text=self.left_axis_labels[index - 1], units=self.left_axis_units[index - 1])
			self.sensorplot.setLabel('bottom', text=self.bottom_axis_label)
		else:
			self.sensorplot.setTitle("null")

	def showwindow(self, index):
		self.windows[index].show()

	def gsm_filtergraph(self, index):
		if self.graph_type == 1:
			if (GSM_PT_LABELS[index] in self.filter_list):
				self.filter_list.remove(GSM_PT_LABELS[index])
			else:
				self.filter_list.append(GSM_PT_LABELS[index])
		elif self.graph_type == 2:
			if (GSM_TC_LABELS[index] in self.filter_list):
				self.filter_list.remove(GSM_TC_LABELS[index])
			else:
				self.filter_list.append(GSM_TC_LABELS[index])
		elif self.graph_type == 3:
			if (GSM_LC_LABELS[index] in self.filter_list):
				self.filter_list.remove(GSM_LC_LABELS[index])
			else:
				self.filter_list.append(GSM_LC_LABELS[index])

	def fsm_filtergraph(self, index):
		if self.graph_type == 1:
			if (FSM_PT_LABELS[index] in self.filter_list):
				self.filter_list.remove(FSM_PT_LABELS[index])
			else:
				self.filter_list.append(FSM_PT_LABELS[index])
		elif self.graph_type == 2:
			if (FSM_TC_LABELS[index] in self.filter_list):
				self.filter_list.remove(FSM_TC_LABELS[index])
			else:
				self.filter_list.append(FSM_TC_LABELS[index])
		elif self.graph_type == 3:
			if (FSM_LC_LABELS[index] in self.filter_list):
				self.filter_list.remove(FSM_LC_LABELS[index])
			else:
				self.filter_list.append(FSM_LC_LABELS[index])

	def refresh(self):
		self.update_menubar()
		
		self.statusbar.showMessage("GSM: " + self.return_status(self.gsm_state) + " | " + "FSM: " + self.return_status(self.fsm_state))

		if self.graph_ready:
			self.sensorplot.clear()

			self.clear_label()

			if self.gsm_state:
				for i in range (0, len(self.graph_gsm_sensor)):
					if not self.graph_gsm_labels[i] in self.filter_list:
						self.legend.addItem(self.sensorplot.plot(self.graph_gsm_time, self.graph_gsm_sensor[i], pen=(i,len(self.graph_gsm_sensor) + len(self.graph_gsm_sensor)), name = self.graph_gsm_labels[i]), self.graph_gsm_labels[i])

			if self.fsm_state:
				for i in range (0, len(self.graph_fsm_sensor)):
					if not self.graph_fsm_labels[i] in self.filter_list:
						self.legend.addItem(self.sensorplot.plot(self.graph_fsm_time, self.graph_fsm_sensor[i], pen=(i,len(self.graph_fsm_sensor) + len(self.graph_fsm_sensor)), name = self.graph_fsm_labels[i]), self.graph_fsm_labels[i])
			self.graph_ready = False
			self.viewbox.setMaximumWidth(self.legend.boundingRect().width())

		else:
			pass

	def clear_label(self):
		for i in GSM_PT_LABELS:
			self.legend.removeItem(i)
		for i in FSM_PT_LABELS:
			self.legend.removeItem(i)
		for i in GSM_TC_LABELS:
			self.legend.removeItem(i)
		for i in FSM_TC_LABELS:
			self.legend.removeItem(i)

	def update_menubar(self):
		if self.gui_update:
			if self.gsm_state == False:
				if (self.graph_type == 1):
					self.MenuBar(GSM_PT_LABELS, FSM_PT_LABELS)
				elif (self.graph_type == 2):
					self.MenuBar(GSM_TC_LABELS, FSM_TC_LABELS)
				elif (self.graph_type == 3):
					self.MenuBar(GSM_LC_LABELS, FSM_LC_LABELS)
			elif self.fsm_state == False:
				if (self.graph_type == 1):
					self.MenuBar(GSM_PT_LABELS, FSM_PT_LABELS)
				elif (self.graph_type == 2):
					self.MenuBar(GSM_TC_LABELS, FSM_TC_LABELS)
				elif (self.graph_type == 3):
					self.MenuBar(GSM_LC_LABELS, FSM_LC_LABELS)
			self.gui_update = False

	def return_status(self, status):
		if status:
			return "Online"
		else:
			return "Offline"


class PopUpWindow(QtWidgets.QMainWindow):

	def __init__(self, GraphWindow, graph_type, parent=None):
		super(PopUpWindow, self).__init__()
		self.graph_window = GraphWindow
		self.graph_type = graph_type
		self.form_widget = FormWidget(self, GraphWindow, graph_type)
		self.setStyleSheet("QMainWindow {background: 'white';}");
		widget = QtGui.QWidget()
		layout = QtGui.QVBoxLayout(widget)
		layout.addWidget(self.form_widget)
		self.setCentralWidget(widget)
		if (graph_type == 1):
			self.setWindowTitle('Pressure Transducer')
		elif (graph_type == 2):
			self.setWindowTitle('Thermocouple')
		elif (graph_type == 3):
			self.setWindowTitle('Load Cell')
		else:
			self.setWindowTitle('null')


class FormWidget(QtWidgets.QWidget):

	def __init__(self, parent, GraphWindow, graph_type):
		super(FormWidget, self).__init__(parent)
		self.graph_window = GraphWindow
		self.graph_type = graph_type

		# Set up widgets
		self.textbox1 = QtWidgets.QLabel(self)
		self.textbox2 = QtWidgets.QLabel(self)
		font = QtGui.QFont("Arial", 12, QtGui.QFont.Bold)
		self.textbox1.setFont(font)
		self.textbox2.setFont(font)
		self.layout()

		# Update the graph
		self.timer = QtCore.QTimer(self)
		self.timer.setInterval(0) # in milliseconds
		self.timer.start()
		self.timer.timeout.connect(self.refresh)

	def layout(self):
		self.vbox = QtGui.QVBoxLayout()
		self.hbox = QtGui.QHBoxLayout()

		self.hbox.addWidget(self.textbox1)
		self.hbox.addWidget(self.textbox2)

		self.vbox.addLayout(self.hbox)
		self.setLayout(self.vbox)

	def refresh(self):
		if self.graph_type == 1:
			self.printvalues(GSM_PT_LABELS, FSM_PT_LABELS, self.graph_window.gsm_pt, self.graph_window.fsm_pt)
		elif self.graph_type == 2:
			self.printvalues(GSM_TC_LABELS, FSM_TC_LABELS, self.graph_window.gsm_tc, self.graph_window.fsm_tc)
		elif self.graph_type == 3:
			self.printvalues(GSM_LC_LABELS, FSM_LC_LABELS, self.graph_window.gsm_lc, self.graph_window.fsm_lc)

	def printvalues(self, gsm_label, fsm_label, gsm_sensor, fsm_sensor):
		if self.graph_window.gsm_state or self.graph_window.fsm_state:
			text1 = "━━━━━━━━━━━━━━\n"
			for i in range (0, len(gsm_sensor)):
				text1 = text1 + gsm_label[i] + "\n" + "━━━━━━━━━━━━━━\n"
			for i in range (0, len(fsm_sensor)):
				text1 = text1 + fsm_label[i] + "\n" + "━━━━━━━━━━━━━━\n"

			text2 = "━━━━━━━━━\n"
			for i in range (0, len(gsm_sensor)):
				if i == 0:
					text2 = text2 + str(round(gsm_sensor[i][len(gsm_sensor[i]) - 1] * 0.9506 - 2.2495, 2)) + "\n" + "━━━━━━━━━\n"
				else:
					text2 = text2 + str(round(gsm_sensor[i][len(gsm_sensor[i]) - 1], 2)) + "\n" + "━━━━━━━━━\n"
			for i in range (0, len(fsm_sensor)):
				text2 = text2 + str(round(fsm_sensor[i][len(fsm_sensor[i]) - 1], 2)) + "\n" + "━━━━━━━━━\n"

			self.textbox1.setText(text1)
			self.textbox2.setText(text2)
		else:
			text = "NO DATA"
			self.textbox1.setText(text)
			self.textbox2.setText(text)

def main():
	app = QtWidgets.QApplication(sys.argv)
	app.setApplicationName('ARES')
	window = GraphWindow()
	#window.resize(1920, 1080)
	window.show()
	app.exec_()

if __name__ == '__main__':
	main()