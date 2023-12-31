import sys
import time
import os
import json

import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
from datetime import datetime

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from threaded_objects.measurement_handler import MeasurementHandler
from threaded_objects.data_handler import DataHandler
from threaded_objects.analysis_handler import AnalysisHandler
from threaded_objects.data_saver import DataSaver

class MainWindow(QMainWindow):
    startSweepMeasurementSignal = pyqtSignal(np.ndarray)
    abortMeasurementSignal = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Measurement flag
        self.isMeasuring = False # this could be useful, but check if it is actually used

        # Setting default path for data analysis
        self.programFolderPath = os.path.abspath(__file__)
        self.workingFolderPath = ""
                
        # Sub-widgets
        self.createInstrumentSettings()
        self.createSweepSettings()
        self.createAnalysisSettings()
        self.createFileSettings()
        self.createMeasurementControlButtons()
        self.createDataDisplayTab()

        # Main UI
        self.setWindowTitle("Dummy JV")
        self.buildMainUI()
        self.statusBar().showMessage("Ready to measure.")

        # Mutex objects
        self.mutexMeasurement = QMutex()
        self.mutexFileSaving = QMutex()

        # Measurement Thread
        self.THREAD_Measurement = QThread()
        self.measurementHandler = MeasurementHandler(self.mutexMeasurement)
        self.measurementHandler.moveToThread(self.THREAD_Measurement)

        self.THREAD_Measurement.start()

        # Data Handler Thread
        self.THREAD_Data = QThread()
        self.dataHandler = DataHandler()
        self.dataHandler.moveToThread(self.THREAD_Data)
        self.THREAD_Data.start()

        # Threadpool
        self.threadpool = QThreadPool()

        # Measurement Handler to Data Handler:
        self.measurementHandler.sendSweepPointSignal.connect(self.dataHandler.buildArrayFromSweepPoints, Qt.QueuedConnection)
        self.measurementHandler.finaliseSweepArraySignal.connect(self.dataHandler.finaliseArray, Qt.QueuedConnection)
        self.measurementHandler.abortMeasurementSignal.connect(self.dataHandler.abortMeasurement)

        # Measurement Handler to Main GUI Thread
        self.measurementHandler.sweepSetStartedSingal.connect(self.respondMeausurementStarted, Qt.QueuedConnection)
        self.measurementHandler.sweepSetFinishedSignal.connect(self.respondForMeasurementFinished, Qt.QueuedConnection)
        self.measurementHandler.abortMeasurementSignal.connect(self.respondForMeasurementFinished, Qt.QueuedConnection)
        self.measurementHandler.sendVocValueSignal.connect(self.updateVocValue, Qt.QueuedConnection)
        self.measurementHandler.measurementVOCStartedSignal.connect(self.respondMeausurementStarted, Qt.QueuedConnection)
        self.measurementHandler.measurementVOCStartedSignal.connect(self.respondForMeasurementFinished, Qt.QueuedConnection)

        # Data Handler to Main GUI Thread
        self.dataHandler.updateGraphSignal.connect(self.plotData, Qt.QueuedConnection)
        self.dataHandler.sendDataArrayForSavingSingal.connect(self.startSaveDataThread, Qt.QueuedConnection)

        # Main GUI Self Connections
        self.controlStartButton.clicked.connect(self.gatekeeperSweepMeasurement, Qt.QueuedConnection)
        self.inputFetchFolderPath.clicked.connect(self.folderBrowse, Qt.QueuedConnection)
        self.inputCellArea.valueChanged.connect(self.gatekeeperAnalysisVariables, Qt.QueuedConnection)
        self.inputPower.valueChanged.connect(self.gatekeeperAnalysisVariables, Qt.QueuedConnection)

        # Main GUI to Measurement Handler
        self.controlMeasureVoc.clicked.connect(self.measurementHandler.measureVOC, Qt.QueuedConnection)
        self.startSweepMeasurementSignal.connect(self.measurementHandler.measureSweep, Qt.QueuedConnection)
        self.controlsStopButton.clicked.connect(self.measurementHandler.abortMeasurement, Qt.DirectConnection) # Direct to interrupt any current processes and set measurement consent to false
        self.abortMeasurementSignal.connect(self.measurementHandler.abortMeasurement, Qt.DirectConnection)

        # Console and Status Connections
        self.measurementHandler.sendConsoleUpdateSignal.connect(self.updateConsole, Qt.QueuedConnection)
        self.measurementHandler.sendStatusUpdateSignal.connect(self.updateStatus, Qt.QueuedConnection)
        self.dataHandler.sendConsoleUpdateSignal.connect(self.updateConsole, Qt.QueuedConnection)
        self.dataHandler.sendStatusUpdateSignal.connect(self.updateStatus, Qt.QueuedConnection)

        self.loadProgramSettings()

    def createInstrumentSettings(self):

        self.InstrumentSettings = QGroupBox("Instrument Settings")
        self.layoutInstrumentSettings = QGridLayout(self.InstrumentSettings)

        self.labelFourOrTwoWire = QLabel("Terminal Settings", self.InstrumentSettings)
        self.inputTerminalSettings = QComboBox(self.InstrumentSettings)
        self.inputTerminalSettings.addItem("Four Wire")
        self.inputTerminalSettings.addItem("Two Wire")

        self.labelFrontOrRearPanel = QLabel("Panel Settings", self.InstrumentSettings)
        self.inputPanelSetting = QComboBox(self.InstrumentSettings)
        self.inputPanelSetting.addItem("Front Banana Connection")
        self.inputPanelSetting.addItem("Rear Triaxial Connection")

        self.layoutInstrumentSettings.addWidget(self.labelFourOrTwoWire, 0, 0)
        self.layoutInstrumentSettings.addWidget(self.inputTerminalSettings, 1, 0)
        self.layoutInstrumentSettings.addWidget(self.labelFrontOrRearPanel, 0, 1)
        self.layoutInstrumentSettings.addWidget(self.inputPanelSetting, 1, 1)

    def createSweepSettings(self):

        self.SweepSettings = QGroupBox("Sweep Settings")
        self.SweepSettings.setMaximumWidth(200)
        self.SweepSettings.setMaximumHeight(250) # Minimum height of QGroupBox, considering the space needed for it's child widgets
        self.layoutSweepSettings = QVBoxLayout(self.SweepSettings)

        self.labelStartVoltage = QLabel("Start Voltage (V)", self.SweepSettings)
        self.inputStartVoltage = QDoubleSpinBox(self.SweepSettings)
        self.inputStartVoltage.setSingleStep(0.01)
        self.inputStartVoltage.setRange(-10, 10)

        self.labelEndVoltage = QLabel("End Voltage (V)", self.SweepSettings)
        self.inputEndVoltage = QDoubleSpinBox(self.SweepSettings)
        self.inputEndVoltage.setSingleStep(0.01)
        self.inputEndVoltage.setRange(-10, 10)

        self.labelScanRate = QLabel("Scan Rate (mV/s)", self.SweepSettings)
        self.inputScanRate = QDoubleSpinBox(self.SweepSettings)
        self.inputScanRate.setSingleStep(0.01)
        self.inputScanRate.setMinimum(0)
        self.inputScanRate.setMaximum(2000)

        self.labelRepeats = QLabel("# of Repeats", self.SweepSettings)
        self.inputRepeats = QSpinBox(self.SweepSettings)
        self.inputRepeats.setMinimum(1)
        self.inputRepeats.setMaximum(10000) # why not

        self.labelSweepType = QLabel("Sweep Type", self.SweepSettings)
        self.inputSweepType = QComboBox(self.SweepSettings)
        self.inputSweepType.addItem("Standard")
        self.inputSweepType.addItem("Hysteresis")

        self.layoutSweepSettings.addWidget(self.labelStartVoltage)
        self.layoutSweepSettings.addWidget(self.inputStartVoltage)
        self.layoutSweepSettings.addWidget(self.labelEndVoltage)
        self.layoutSweepSettings.addWidget(self.inputEndVoltage)
        self.layoutSweepSettings.addWidget(self.labelScanRate)
        self.layoutSweepSettings.addWidget(self.inputScanRate)
        self.layoutSweepSettings.addWidget(self.labelRepeats)
        self.layoutSweepSettings.addWidget(self.inputRepeats)
        self.layoutSweepSettings.addWidget(self.labelSweepType)
        self.layoutSweepSettings.addWidget(self.inputSweepType)
        
    def createAnalysisSettings(self):

        self.MeasurementSettings = QGroupBox("Analysis Settings")
        self.MeasurementSettings.setMaximumWidth(self.SweepSettings.maximumWidth())
        self.MeasurementSettings.setMaximumHeight(self.SweepSettings.maximumHeight())
        self.layoutMeasurementSettings = QVBoxLayout(self.MeasurementSettings)

        self.labelCellArea = QLabel("Cell Area (cm2)", self.MeasurementSettings)
        self.inputCellArea = QDoubleSpinBox(self.MeasurementSettings)
        self.inputCellArea.setSingleStep(0.01)
        self.inputCellArea.setMinimum(0)

        self.labelPower = QLabel("Power Input (uWcm-2)", self.MeasurementSettings)
        self.inputPower = QDoubleSpinBox(self.MeasurementSettings)
        self.inputPower.setSingleStep(0.01)
        self.inputPower.setMinimum(0)

        self.layoutMeasurementSettings.addWidget(self.labelCellArea)
        self.layoutMeasurementSettings.addWidget(self.inputCellArea)
        self.layoutMeasurementSettings.addWidget(self.labelPower)
        self.layoutMeasurementSettings.addWidget(self.inputPower)
        self.layoutMeasurementSettings.addStretch()

    def createFileSettings(self):

        self.FileSettings = QGroupBox("File I/O Settings")
        self.layoutFileSettings = QGridLayout(self.FileSettings)

        # Sub-widget for the inputting the name of the cell
        self.masterInputCellName = QWidget()
        self.layoutMasterInputCellName = QVBoxLayout(self.masterInputCellName)
        self.labelCellName = QLabel("Cell Name", self.masterInputCellName)
        self.inputCellName = QLineEdit(self.masterInputCellName)
        self.layoutMasterInputCellName.addWidget(self.labelCellName)
        self.layoutMasterInputCellName.addWidget(self.inputCellName)

        # Sub-widget for button that calls the folder path selector
        self.masterInputFetchFolderPath = QWidget()
        self.layoutMasterInputFetchFolderPath = QVBoxLayout(self.masterInputFetchFolderPath)
        self.labelFetchFolderPath = QLabel("Working Folder Path", self.masterInputFetchFolderPath)
        self.inputFetchFolderPath = QPushButton("Select...", self.masterInputFetchFolderPath)
        self.layoutMasterInputFetchFolderPath.addWidget(self.labelFetchFolderPath)
        self.layoutMasterInputFetchFolderPath.addWidget(self.inputFetchFolderPath)

        # Sub-widget for the folder path display
        self.masterDisplayFolderPath = QWidget()
        self.layoutMasterDisplayFolderPath = QVBoxLayout(self.masterDisplayFolderPath)
        self.labelDisplayFolderPath = QLabel("Working Folder Path", self.masterDisplayFolderPath)
        self.displayWorkingFolderPath = QPlainTextEdit(self.masterDisplayFolderPath)
        self.displayWorkingFolderPath.setPlainText(self.workingFolderPath)
        self.displayWorkingFolderPath.setReadOnly(True)
        self.displayWorkingFolderPath.setMaximumHeight(300)
        self.layoutMasterDisplayFolderPath.addWidget(self.labelDisplayFolderPath)
        self.layoutMasterDisplayFolderPath.addWidget(self.displayWorkingFolderPath, 1) # 1 = strech factor, so disply box streches until maximum height.
        self.layoutMasterDisplayFolderPath.addStretch()
        
        self.layoutFileSettings.addWidget(self.masterInputCellName, 0, 0)
        self.layoutFileSettings.addWidget(self.masterInputFetchFolderPath, 0, 1)
        self.layoutFileSettings.addWidget(self.masterDisplayFolderPath, 1, 0, 1, 2)

    def createMeasurementControlButtons(self):

        self.MeasurementControls = QGroupBox()
        self.layoutMeasurementControls = QHBoxLayout(self.MeasurementControls)

        self.controlStartButton = QPushButton("Start Measurement", self.MeasurementControls)
        self.controlsStopButton = QPushButton("Stop Measurement", self.MeasurementControls)
        self.controlMeasureVoc = QPushButton("Measure Voc", self.MeasurementControls)
        self.labelVocValue = QLabel("Voc: NaN", self.MeasurementControls)

        self.controlsStopButton.setEnabled(False)

        self.layoutMeasurementControls.addWidget(self.controlStartButton)
        self.layoutMeasurementControls.addWidget(self.controlsStopButton)
        self.layoutMeasurementControls.addWidget(self.controlMeasureVoc)
        self.layoutMeasurementControls.addWidget(self.labelVocValue)
    
    def createDataDisplayTab(self):
 
        # Graph Tab Layout
        self.graphTab = QWidget()
        self.layoutGraphTab = QVBoxLayout(self.graphTab)
        self.figure = Figure()
        self.canvasWidget = FigureCanvas(self.figure)
        self.layoutGraphTab.addWidget(self.canvasWidget)

        # Table Tab Layout
        self.tableTab = QWidget()
        self.layoutTableTab = QVBoxLayout(self.tableTab)
        self.tableWidget = QTableWidget(self.tableTab)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(["Cell Name", "Voc", "Jsc", "FF", "Efficiency"])
        self.layoutTableTab.addWidget(self.tableWidget)

        # Console Tab Layout
        self.consoleTab = QWidget()
        self.layoutConsoleTab = QVBoxLayout(self.consoleTab)
        self.console = QPlainTextEdit(self.consoleTab)
        self.console.setReadOnly(True)
        self.layoutConsoleTab.addWidget(self.console)

        # Tab layout (with graph and console)
        self.tabControl = QTabWidget()
        self.tabControl.addTab(self.graphTab, "Graph")
        self.tabControl.addTab(self.tableTab, "Table")
        self.tabControl.addTab(self.consoleTab, "Console")

    def buildMainUI(self):

        self.mainWidget = QWidget()

        # Main layout
        self.mainLayout = QGridLayout(self.mainWidget)
        self.mainLayout.addWidget(self.InstrumentSettings, 0, 0, 1, 2)
        self.mainLayout.addWidget(self.SweepSettings, 1, 0)
        self.mainLayout.addWidget(self.MeasurementSettings, 1, 1)
        self.mainLayout.addWidget(self.FileSettings, 2, 0, 1, 2)
        self.mainLayout.addWidget(self.MeasurementControls, 3, 0, 1, 2)
        self.mainLayout.addWidget(self.tabControl, 0, 3, 4, 4)

        # Building and showing main widget
        self.setCentralWidget(self.mainWidget)
        self.show()

    def saveProgramSettings(self, _savePath="programSettings.json"):

        # Instrument Settings
        _terminalSetting = self.inputTerminalSettings.currentText()
        _panelSetting = self.inputPanelSetting.currentText()

        # Sweep setting
        _startVoltage = self.inputStartVoltage.value()
        _endVoltage = self.inputEndVoltage.value()
        _scanRate = self.inputScanRate.value()
        _repeats = self.inputRepeats.value()
        _sweepType = self.inputSweepType.currentText()

        # Analysis settings
        _cellArea = self.inputCellArea.value()
        _power = self.inputPower.value()

        # File I/O settings
        _cellName = self.inputCellName.text()
        _workingFolderPath = self.workingFolderPath

        _settings = {
            "Instrument Settings": {
                "Terminal Setting": _terminalSetting,
                "Panel Setting": _panelSetting
            },
            "Sweep Settings": {
                "Start Voltage": _startVoltage,
                "End Voltage": _endVoltage,
                "Scan Rate": _scanRate,
                "Repeats": _repeats,
                "Sweep Type": _sweepType
            },
            "Analysis Settings": {
                "Cell Area": _cellArea,
                "Power": _power
            },
            "File I/O Settings": {
                "Cell Name": _cellName, 
                "Working Folder Path": _workingFolderPath
            }
        }

        with open(_savePath, "w") as file:
            json.dump(_settings, file, indent=4)

    def loadProgramSettings(self):
        try:
            with open("programSettings.json", "r") as file:
                _settings = json.load(file)

            # Instrument Settings
            self.inputTerminalSettings.setCurrentText(_settings["Instrument Settings"]["Terminal Setting"])
            self.inputPanelSetting.setCurrentText(_settings["Instrument Settings"]["Panel Setting"])

            # Sweep settings
            self.inputStartVoltage.setValue(_settings["Sweep Settings"]["Start Voltage"])
            self.inputEndVoltage.setValue(_settings["Sweep Settings"]["End Voltage"])
            self.inputScanRate.setValue(_settings["Sweep Settings"]["Scan Rate"])
            self.inputRepeats.setValue(_settings["Sweep Settings"]["Repeats"])
            self.inputSweepType.setCurrentText(_settings["Sweep Settings"]["Sweep Type"])

            # Analysis settings
            self.inputCellArea.setValue(_settings["Analysis Settings"]["Cell Area"])
            self.inputPower.setValue(_settings["Analysis Settings"]["Power"])

            # File I/O settings
            self.inputCellName.setText(_settings["File I/O Settings"]["Cell Name"])
            self.workingFolderPath = _settings["File I/O Settings"]["Working Folder Path"]
            self.displayWorkingFolderPath.setPlainText(self.workingFolderPath)

        except:
            self.updateConsole("WARNING: Error reading programSettings.json, the file likely does not exist or has invalid values, setting default values.")

            # Defaults
            self.inputStartVoltage.setValue(1.05)
            self.inputEndVoltage.setValue(-0.05)
            self.inputScanRate.setValue(10)
            self.inputRepeats.setValue(1)

    @pyqtSlot(np.ndarray)
    def startSaveDataThread(self, dataArray):
        """
        CALLED FROM: DataHandler
        CALL PATH: MainWindow (gatekeeperStartMeasurement) -> MeasurementHandler (measureSweep) -> DataHandler (finaliseArray) -> Here
        """

        _analysisSettings = np.empty([1, 2])
        _analysisSettings[0, 0] = self.inputCellArea.value()
        _analysisSettings[0, 1] = self.inputPower.value()

        saveDataTask = DataSaver(self.mutexFileSaving, dataArray, self.sweepProperties, _analysisSettings, self.inputCellName.text(), self.workingFolderPath)
        self.threadpool.start(saveDataTask)
        self.threadpool.waitForDone()

    @pyqtSlot()
    def respondMeausurementStarted(self):
        """
        SLOT CALLED FROM: MeasurementHandler
        """
        self.isMeasuring = True
        self.statusBar().showMessage("Measuring JV sweep...")
 
        # Measurement control buttons
        self.controlStartButton.setEnabled(False)
        self.controlsStopButton.setEnabled(True)
        self.controlMeasureVoc.setEnabled(False)
        
        # Analysis variables
        self.inputCellArea.setEnabled(False)
        self.inputPower.setEnabled(False)

        # Sweep settings
        self.inputStartVoltage.setEnabled(False)
        self.inputEndVoltage.setEnabled(False)
        self.inputScanRate.setEnabled(False)
        self.inputRepeats.setEnabled(False)
        self.inputSweepType.setEnabled(False)

        # Folder I/O setting
        self.inputFetchFolderPath.setEnabled(False)
        self.inputCellName.setEnabled(False)

        # Insturment settings
        self.inputPanelSetting.setEnabled(False)
        self.inputTerminalSettings.setEnabled(False)
    
    @pyqtSlot()
    def respondForMeasurementFinished(self):
        self.isMeasuring = False
        self.statusBar().showMessage("Measurement finished, ready to measure.")
        
        # Measurement control buttons
        self.controlStartButton.setEnabled(True)
        self.controlsStopButton.setEnabled(False)
        self.controlMeasureVoc.setEnabled(True)
        
        # Analysis variables
        self.inputCellArea.setEnabled(True)
        self.inputPower.setEnabled(True)

        # Sweep settings
        self.inputStartVoltage.setEnabled(True)
        self.inputEndVoltage.setEnabled(True)
        self.inputScanRate.setEnabled(True)
        self.inputRepeats.setEnabled(True)
        self.inputSweepType.setEnabled(True)

        # Folder I/O setting
        self.inputFetchFolderPath.setEnabled(True)
        self.inputCellName.setEnabled(True)

        # Insturment settings
        self.inputPanelSetting.setEnabled(True)
        self.inputTerminalSettings.setEnabled(True)
    
    @pyqtSlot(str)
    def updateConsole(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}]:\n{message}\n"
        self.console.appendPlainText(formatted_message)

    @pyqtSlot(str)
    def updateStatus(self, message):
        self.statusBar().showMessage(message)

    @pyqtSlot(float)
    def updateVocValue(self, value):
        self.valueVoc = value * 1000
        self.labelVocValue.setText(f"Voc: {self.valueVoc:.0f} mV")

    @pyqtSlot(np.ndarray)
    def plotData(self, dataToPlot):
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        ax.plot(dataToPlot[:,0], dataToPlot[:,1], "kx-")
        ax.grid()
        ax.set_xlabel("Voltage (V)")
        ax.set_ylabel("Current (A)")
        self.canvasWidget.draw()

    @pyqtSlot()    
    def shutdown(self):

        self.saveProgramSettings()
        self.abortMeasurementSignal.emit()
        time.sleep(1) # Saftey wait, paranoid step to give threads time to recieve signals to quit

        self.THREAD_Measurement.quit()
        self.THREAD_Measurement.wait()
        self.THREAD_Data.quit()
        self.THREAD_Data.wait()
        time.sleep(0.5) # Saftey wait, paranoid step to give everything time to fully shut down.

    @pyqtSlot()
    def gatekeeperAnalysisVariables(self):
        _cellArea = self.inputCellArea.value()
        _powerIn = self.inputPower.value()

        _analysisVariables = np.empty([1, 2])
        _analysisVariables = [_cellArea, _powerIn]

        #self.sendAnalysisVariablesSignal.emit()

    @pyqtSlot()
    def gatekeeperSweepMeasurement(self):
        """Checks if there is a valid path to save data to. Packs the current sweep settings into an array and sends it to the measurement thread."""

        # Check if a folder path has been selected.
        if self.workingFolderPath:

            # Check if folder path exists.
            if os.path.isdir(self.workingFolderPath):
                _startVoltage = self.inputStartVoltage.value() 
                _endVoltage =  self.inputEndVoltage.value()
                _repeats = self.inputRepeats.value()
                _scanRate = self.inputScanRate.value()
                self.sweepProperties = np.empty([1, 4])
                self.sweepProperties[0, :] = [_startVoltage, _endVoltage, _repeats, _scanRate]

                self.startSweepMeasurementSignal.emit(self.sweepProperties)
            else:
                self.displayAlertBox("A folder path is selected but it is not valid for this computer.\nDid you load the configuration file from another machine?")
        else:
            self.displayAlertBox("The working folder path not selected! A working folder path must be set before starting a measurement!")

    def displayAlertBox(text):
        """Display a pop-up warning box"""
        self.AlertBox = QMessageBox()
        self.AlertBox.setWindowTitle("Warning!")
        self.AlertBox.setText(text)
        self.AlertBox.exec_()

    @pyqtSlot()
    def folderBrowse(self):
        self.workingFolderPath = QFileDialog.getExistingDirectory(self, "Select Folder")
        self.displayWorkingFolderPath.setPlainText(self.workingFolderPath)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    app.aboutToQuit.connect(window.shutdown, Qt.DirectConnection) # Direct connection to ensure the shutdown method is ran immediately.
    app.exec()

main()