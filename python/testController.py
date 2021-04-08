""" pytester.py is an application built by request of RocketLab as part of a job application.
This application allows the user to:
- connect with a test device at a specified IP address on a specified port
- define test duration
- start a test
- force a test to stop early
- see a live plot of measured values during the test
- write test results to a PDF containing the plotted data and some information about the test.
Authored by Harry Hebden 2021
"""
import os
import sys
import select

from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox, QDockWidget, QPlainTextEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, QRect, QTimer, Qt

import pyqtgraph
import socket

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pandas import DataFrame

from datetime import datetime

class DeviceTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'RocketLab Device Tester'
        self.left = 10
        self.top = 10
        self.width = 1200
        self.height = 600
        self.connectionEstablished = False
        self.milliVoltsList = []
        self.milliAmpsList = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.mainHorizontalLayout = QHBoxLayout()
        self.leftVerticalLayout = QVBoxLayout()
        self.rightVericalLayout = QVBoxLayout()
        self.mainHorizontalLayout.addLayout(self.leftVerticalLayout)
        self.mainHorizontalLayout.addLayout(self.rightVericalLayout)

        self.createConnectionLayout()
        self.createDeviceTestLayout()
        self.createReportOutputLayout()
        self.createGraphLayout()
        self.createStatusPane()

        widget = QWidget()
        widget.setLayout(self.mainHorizontalLayout)
        self.setCentralWidget(widget)

        self.clearTestData()
        self.dataLineMilliVolts = self.resultsGraph.plot(self.graphTimeVals, self.graphMilliVoltVals, pen=self.graphRedPen)
        self.dataLineMilliAmps = self.resultsGraph.plot(self.graphTimeVals, self.graphMilliAmpVals, pen=self.graphGreenPen)
        self.clearGraphLine()

        self.show()


    def createConnectionLayout(self):
        self.ConnectLabel = QLabel("IP Address of Test Device (IPv4):Port", self)
        self.ConnectLabel.resize(150, 30)

        self.IPAddressTextbox = QLineEdit(self)
        self.IPAddressTextbox.setText("127.0.0.1:49181")
        self.IPAddressTextbox.resize(150, 30)

        self.ConnectButton = QPushButton('Connect', self)
        self.ConnectButton.clicked.connect(self.on_connect_click)

        self.connectionLayout = QHBoxLayout()
        self.connectionLayout.addWidget(self.ConnectLabel)
        self.connectionLayout.addWidget(self.IPAddressTextbox)
        self.connectionLayout.addWidget(self.ConnectButton)
        self.leftVerticalLayout.addLayout(self.connectionLayout)

    def createDeviceTestLayout(self):
        self.testDurationLabel = QLabel("Duration of Test (seconds):", self)
        self.testDurationLabel.resize(150, 30)

        self.testDurationTextbox = QLineEdit(self)
        self.testDurationTextbox.resize(150, 30)
        self.testDurationTextbox.setText("3")

        self.testRateLabel = QLabel("Rate of Test (ms):", self)
        self.testRateLabel.resize(150, 30)

        self.testRateTextbox = QLineEdit(self)
        self.testRateTextbox.resize(150, 30)
        self.testRateTextbox.setText("100")

        self.testStartButton = QPushButton('Start', self)
        self.testStartButton.clicked.connect(self.on_test_start_click)

        self.testStopButton = QPushButton('Stop', self)
        self.testStopButton.clicked.connect(self.on_test_stop_click)

        self.deviceTestLayout = QHBoxLayout()
        self.deviceTestLayout.addWidget(self.testDurationLabel)
        self.deviceTestLayout.addWidget(self.testDurationTextbox)
        self.deviceTestLayout.addWidget(self.testRateLabel)
        self.deviceTestLayout.addWidget(self.testRateTextbox)
        self.deviceTestLayout.addWidget(self.testStartButton)
        self.deviceTestLayout.addWidget(self.testStopButton)
        self.leftVerticalLayout.addLayout(self.deviceTestLayout)

    def createReportOutputLayout(self):
        self.reportSavePathLabel = QLabel("Filepath for report:", self)
        self.reportSavePathLabel.resize(150, 30)

        self.reportSavePathTextbox = QLineEdit(self)
        self.reportSavePathTextbox.resize(150, 30)
        self.reportSavePathTextbox.setText(os.getcwd() + "/")

        self.generateReportButton = QPushButton('Generate Report', self)
        self.generateReportButton.clicked.connect(self.on_generate_report_click)

        self.clearGraphButton = QPushButton('Clear', self)
        self.clearGraphButton.clicked.connect(self.on_clear_graph_click)

        self.reportOutputLayout = QHBoxLayout()
        self.reportOutputLayout.addWidget(self.reportSavePathLabel)
        self.reportOutputLayout.addWidget(self.reportSavePathTextbox)
        self.reportOutputLayout.addWidget(self.generateReportButton)
        self.reportOutputLayout.addWidget(self.clearGraphButton)
        self.leftVerticalLayout.addLayout(self.reportOutputLayout)

    def createGraphLayout(self):
        self.resultsGraph = pyqtgraph.PlotWidget()
        self.resultsGraph.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.resultsGraph)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.addWidget(self.resultsGraph)

        self.resultsGraph.setTitle("Test Results")
        self.resultsGraph.setLabel("left", "MilliVolts (mV)", **{"color":"#f00", "font-size":"15px"})
        self.resultsGraph.setLabel("right", "MilliAmps (mA)", **{"color":"#0f0", "font-size":"15px"})
        self.resultsGraph.setLabel("bottom", "Time since Test Start (mS)")
        self.resultsGraph.setGeometry(QRect(350,20,450,350))

        self.graphLayout = QHBoxLayout()
        self.graphLayout.addWidget(self.resultsGraph)
        self.rightVericalLayout.addLayout(self.graphLayout)

        self.graphRedPen = pyqtgraph.mkPen('r', width=1)
        self.graphGreenPen = pyqtgraph.mkPen('g', width=1)

    def createStatusPane(self):
        self.statusBox = QPlainTextEdit()
        self.statusBox.setReadOnly(True)
        self.statusBox.resize(50,50)
        self.statusLayout = QHBoxLayout()
        self.statusLayout.addWidget(self.statusBox)
        self.leftVerticalLayout.addLayout(self.statusLayout)

    def getNewData(self):
        if "TIME=" in self.statusMessage:
            self.startTimeString = self.statusMessage.find('=',0,len(self.statusMessage))
            self.endTimeString = self.statusMessage.find(';MV',0,len(self.statusMessage))
            self.timeElapsed = self.statusMessage[self.startTimeString+1:self.endTimeString]

            self.startVoltString = self.statusMessage.find('=',self.endTimeString,len(self.statusMessage))
            self.endVoltString = self.statusMessage.find(';MA',self.endTimeString,len(self.statusMessage))
            self.milliVolts = self.statusMessage[self.startVoltString+1:self.endVoltString]

            self.startAmpString = self.statusMessage.find('=',self.endVoltString,len(self.statusMessage))
            self.endAmpString = self.statusMessage.find(';',self.endVoltString+3,len(self.statusMessage))
            self.milliAmps = self.statusMessage[self.startAmpString+1:self.endAmpString]
            self.updateGraphData()
            self.updateStoredData()

    def updateGraphData(self):
        self.graphTimeVals = self.graphTimeVals[1:]
        self.graphTimeVals.append(int(float(self.timeElapsed)))
        self.graphMilliVoltVals = self.graphMilliVoltVals[1:]
        self.graphMilliVoltVals.append(int(float(self.milliVolts)))
        self.graphMilliAmpVals = self.graphMilliAmpVals[1:]
        self.graphMilliAmpVals.append(int(float(self.milliAmps)))
        self.dataLineMilliVolts.setData(self.graphTimeVals, self.graphMilliVoltVals)
        self.dataLineMilliAmps.setData(self.graphTimeVals, self.graphMilliAmpVals)

    def updateStoredData(self):
        if len(self.timeList) == 0:
            self.timeList.append(0)
        else:
            self.timeList.append(int(float(self.timeElapsed)))
        self.milliVoltsList.append(int(float(self.milliVolts)))
        self.milliAmpsList.append(int(float(self.milliAmps)))

    def checkMessages(self):
        ready = select.select([self.target_device_socket], [], [], 0.25)
        if ready[0]:
            self.data, self.addr = self.target_device_socket.recvfrom(1024)
            self.statusMessage = f"{self.data.decode('latin1')}"
            self.statusBox.insertPlainText(self.statusMessage + "\n")
            self.statusBox.verticalScrollBar().setValue(self.statusBox.verticalScrollBar().maximum())
            self.getNewData()
            self.data = ''
            ready=['']

    def createStatusUpdater(self):
        self.statusUpdateTimer = QTimer()
        self.statusUpdateTimer.setInterval(1)
        self.statusUpdateTimer.timeout.connect(self.checkMessages)
        self.statusUpdateTimer.start()

    def sendByteMessage(self, messageString):
        byte_message = bytes(messageString, "latin1")
        self.target_device_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target_device_socket.sendto(byte_message, (self.deviceIPAddress, self.devicePortNumber))

    def clearTestData(self):
        self.graphTimeVals =  [0] * 20
        self.graphMilliVoltVals = [0] * 20
        self.graphMilliAmpVals  = [0] * 20
        self.timeList = []
        self.milliVoltsList = []
        self.milliAmpsList = []

    def clearGraphLine(self):
        self.dataLineMilliVolts.clear()
        self.dataLineMilliAmps.clear()
        self.dataLineMilliVolts.setData(self.graphTimeVals, self.graphMilliVoltVals)
        self.dataLineMilliAmps.setData(self.graphTimeVals, self.graphMilliAmpVals)

    def logMessage(self, logMessageString):
        print(logMessageString)
        self.statusBox.insertPlainText(logMessageString)

    def createReport(self):
        now = datetime.now()
        dateTimeString = now.strftime("%Y_%m_%d_%H_%M_%S")
        reportFilename = "RL_Test_Report_" + dateTimeString + ".pdf"
        fullFilePath = self.filePath + reportFilename

        testResultsTimeSeries = {'Time of Sample': self.timeList,
                        'MilliVolts': self.milliVoltsList,
                        'MilliAmps': self.milliAmpsList
                        }
        testResultsDataFrame = DataFrame(testResultsTimeSeries, columns=['Time of Sample', 'MilliVolts', 'MilliAmps'])

        with PdfPages(fullFilePath) as export_pdf:
            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()
            ax1.plot(testResultsDataFrame['Time of Sample'], testResultsDataFrame['MilliVolts'], color='red', marker='o')
            ax2.plot(testResultsDataFrame['Time of Sample'], testResultsDataFrame['MilliAmps'], color='green', marker='o')
            plt.title('Test results')
            ax1.set_xlabel('Time of Sample (ms)')
            ax1.set_ylabel('MilliVolts (mV)', color='red')
            ax2.set_ylabel('MilliAmps (mA)', color='green')
            plt.grid(True)
            fig.tight_layout()
            plt.show()
            export_pdf.savefig()
            plt.close()

    def isIPv4(self, s):
        try: return str(int(s)) == s and 0 <= int(s) <= 255
        except: return False

    @pyqtSlot()
    def on_connect_click(self):
        self.deviceIPAddress = self.IPAddressTextbox.text().split(':')[0]
        self.devicePortNumber = self.IPAddressTextbox.text().split(':')[1]
        try:
            if (self.deviceIPAddress.count(".") == 3 and all(self.isIPv4(i) for i in self.deviceIPAddress.split(".")) and int(self.devicePortNumber) < 65536):
                self.devicePortNumber = int(self.devicePortNumber)
                try:
                    self.target_device_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.logMessage("[INFO] Successful connection established with " + self.deviceIPAddress + ":" + str(self.devicePortNumber) + "\n")
                    self.target_device_socket.setblocking(0)
                    self.target_device_socket.settimeout(0)
                    self.createStatusUpdater()
                    self.connectionEstablished = True
                except socket.error as e:
                    self.connectionEstablished = False
                    print(e)
            else:
                self.logMessage("[ERROR] IP Address or Port number is invalid. Ensure they follow the correct format, e.g. 127.0.0.1:49181 \n")
        except:
            self.logMessage("[ERROR] IP Address or Port number is invalid. Ensure they follow the correct format, e.g. 127.0.0.1:49181 \n")

    @pyqtSlot()
    def on_test_start_click(self):
        if (self.connectionEstablished == True):
            testDurationValue = self.testDurationTextbox.text()
            testRateValue = self.testRateTextbox.text()
            try:
                int(testDurationValue)
                int(testRateValue)
                self.sendByteMessage(f"TEST;CMD=START;DURATION={testDurationValue};RATE={testRateValue};")
            except ValueError:
                self.logMessage("[ERROR] Values for Duration of Test and Rate of Test must be integers.\n")
                return
        else:
            self.logMessage("[ERROR] Cannot start test while no connection established. Please connect first.\n")
        self.clearTestData()
        self.clearGraphLine()
        return

    @pyqtSlot()
    def on_test_stop_click(self):
        if (self.connectionEstablished == True):
            self.sendByteMessage("TEST;CMD=STOP;")
        else:
            self.logMessage("[ERROR] Cannot stop test while no connection established. Please connect first.\n")

    @pyqtSlot()
    def on_generate_report_click(self):
        self.filePath = self.reportSavePathTextbox.text()
        if (os.path.exists(self.filePath)):
            self.createReport()
        else:
            if (self.filePath == ''):
                self.logMessage("[ERROR] Filepath is blank. Please enter a valid filepath.\n")
            else:
                try:
                    os.makedirs(self.filePath)
                    self.createReport()
                except OSError:
                    self.logMessage(f"[ERROR] Creation of directory at {self.filePath} failed.\n")

    @pyqtSlot()
    def on_clear_graph_click(self):
        self.clearTestData()
        self.clearGraphLine()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = DeviceTester()
    sys.exit(app.exec_())
