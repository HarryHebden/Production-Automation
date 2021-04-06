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

from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox, QDockWidget, QPlainTextEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, QRect, QTimer, Qt

import pyqtgraph

from random import randint # Just for testing purposes, remove before submission

from reportlab.pdfgen.canvas import Canvas # Chosen for pdf output formatting ease.

import socket
import select

class DeviceTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'RocketLab Device Tester'
        self.left = 10
        self.top = 10
        self.width = 825
        self.height = 400
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Setup the main layouts
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

        self.x = [0,250,500,750,1000,1250,1500,1750,2000,2250] # TODO(?) time intervals
        self.y = [5,  6,  8,  9,   2,   3,   7,   8,   6,   8] # TODO Fake test results, need to replace.
        self.dataLine = self.resultsGraph.plot(self.x, self.y)
        self.createGraphUpdater()

        self.show()


    def createConnectionLayout(self):
        self.ConnectLabel = QLabel("IP Address of Test Device:", self)
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

        self.testRateLabel = QLabel("Rate of Test (ms):", self)
        self.testRateLabel.resize(150, 30)

        self.testRateTextbox = QLineEdit(self)
        self.testRateTextbox.resize(150, 30)

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

        self.generateReportButton = QPushButton('Generate Report', self)
        self.generateReportButton.clicked.connect(self.on_generate_report_click)

        self.reportOutputLayout = QHBoxLayout()
        self.reportOutputLayout.addWidget(self.reportSavePathLabel)
        self.reportOutputLayout.addWidget(self.reportSavePathTextbox)
        self.reportOutputLayout.addWidget(self.generateReportButton)
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
        self.resultsGraph.setLabel("bottom", "Time since Test Start (mS)") # **{"color":"#000", "font-size":"15px"}
        self.resultsGraph.setGeometry(QRect(350,20,450,350))

        self.graphLayout = QHBoxLayout()
        self.graphLayout.addWidget(self.resultsGraph)
        self.rightVericalLayout.addLayout(self.graphLayout)

    def createStatusPane(self):
        self.statusBox = QPlainTextEdit()
        self.statusBox.setReadOnly(True)
        self.statusBox.resize(50,50)
        self.statusLayout = QHBoxLayout()
        self.statusLayout.addWidget(self.statusBox)
        self.leftVerticalLayout.addLayout(self.statusLayout)

    def updateGraphData(self):
        self.x = self.x[1:] # Remove the oldest x element
        self.x.append(self.x[-1] + 250)
        self.y = self.y[1:] # Remove the oldest y element
        self.y.append(randint(0,10))
        self.dataLine.setData(self.x, self.y) # Update the displayed data.

    def createGraphUpdater(self):
        self.graphUpdateTimer = QTimer()
        self.graphUpdateTimer.setInterval(250) # TODO Change with input testing rate?
        self.graphUpdateTimer.timeout.connect(self.updateGraphData)
        self.graphUpdateTimer.start()

    def createStatusUpdater(self):
        self.statusUpdateTimer = QTimer()
        self.statusUpdateTimer.setInterval(250) # TODO Change with input testing rate?
        self.statusUpdateTimer.timeout.connect(self.checkMessages)
        self.statusUpdateTimer.start()

    @pyqtSlot()
    def on_generate_report_click(self):
        print("TODO implement generate output report")
        # Check for valid entry
        # if (!os.path.exists(self.reportSavePathTextbox.text())):

    @pyqtSlot()
    def on_connect_click(self):
        self.deviceIPAddress = self.IPAddressTextbox.text().split(':')[0]
        self.devicePortNumber = int(self.IPAddressTextbox.text().split(':')[1])
        # TODO Check for valid entry of values
        print("TODO implement connect")


    @pyqtSlot()
    def on_test_start_click(self):
        testDurationValue = self.testDurationTextbox.text()
        testRateValue = self.testRateTextbox.text()
        # TODO Check for valid entry values
        print("TODO implement test start")


    @pyqtSlot()
    def on_test_stop_click(self):
        # TODO Check for valid entry values
        print("TODO Implement test stop")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = DeviceTester()
    sys.exit(app.exec_())
