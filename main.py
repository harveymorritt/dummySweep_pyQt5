import sys
import random
import time
import os

import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
from datetime import datetime

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas



class MeasurementHandler(QObject):
    sendVocValueSignal = pyqtSignal(float)
    sendSweepPointSignal = pyqtSignal(np.ndarray)
    measurementSweepStartedSingal = pyqtSignal()
    measurementSweepFinishedSignal = pyqtSignal()
    measurementVOCStartedSignal = pyqtSignal()
    measurementVOCFinishedSignal = pyqtSignal()
    sendConsoleUpdateSignal = pyqtSignal(str)

    def __init__(self, mutexMeasurement):
        super().__init__()
        self.mutexMeasurement = mutexMeasurement
        self.validState = True
        self.measurementValid = True

        self.sendConsoleUpdateSignal.emit("Keithley 2450 Initilised")

    @pyqtSlot()
    def measureVOC(self):
        self.sendConsoleUpdateSignal.emit("Voc Measurement Started")
        self.measurementVOCStartedSignal.emit()
        if self.validState:
            _dataPoint = np.round(0.6+((1.05-0.6)*np.random.rand()), 3)
            self.sendVocValueSignal.emit(_dataPoint)
        else:
            pass
            ### Return message measurement not being valid ###
        self.measurementVOCFinishedSignal.emit()
        self.sendConsoleUpdateSignal.emit(f"Voc Measurement Finished\nValue: {_dataPoint:.3f} V")

    @pyqtSlot(np.ndarray)
    def measureSweep(self, sweepSettings):
        self.mutexMeasurement.lock()

        _sweepSettings = sweepSettings
        _startVoltage = _sweepSettings[0, 0]
        _endVoltage = _sweepSettings[0, 1]
        _scanRate = _sweepSettings[0, 2]
        
        _n = 1.5 # ideality factor
        _k = 1.38e-23
        _T = 300
        _I0 = 1e-12
        _q = 1.6e-19

        if self.measurementValid:
            self.sendConsoleUpdateSignal.emit("Sweep Measurement Started")
            self.measurementSweepStartedSingal.emit()

            _sweepPoint = np.empty((1, 2))
            
            _yAxisShift = np.round(0.05+((0.25-0.05)*np.random.rand()), 3)
            _measurementPoints = np.linspace(_startVoltage, _endVoltage, num=250)
            for _voltagePoint in _measurementPoints:

                _sleepTime = 0.045+(0.055-0.045)*np.random.rand()
                time.sleep(_sleepTime)

                _current = _I0*(np.exp((_q * _voltagePoint)/(_n*_k*_T)) - 1)

                _currentError = -0.005+(0.015+0.005)*np.random.rand()

                _sweepPoint[0, 0] = _voltagePoint
                _sweepPoint[0, 1] = _current - _yAxisShift + _currentError
                
                self.sendSweepPointSignal.emit(_sweepPoint.copy()) # .copy() otherwise the for loop "catches up" with the emit signal, and you end up writing over the data being emitted.    
            self.sendConsoleUpdateSignal.emit("Sweep Measurement Finished")
            self.measurementSweepFinishedSignal.emit()

        
        else:
            pass
            # message about not in valid state
        self.mutexMeasurement.unlock()



class DataHandler(QObject):
    updateGraphSignal = pyqtSignal(np.ndarray)
    sendConsoleUpdateSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        
        self.workingArray = []

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sendUpdateGraphSignal, Qt.QueuedConnection)

    @pyqtSlot(np.ndarray)
    def buildArrayFromSweepPoints(self, receivedSweepPoint):
        if not self.timer.isActive():
            self.timer.start(333)
        
        self.workingArray.append(receivedSweepPoint)
    
    @pyqtSlot()
    def finaliseArray(self):
        self.timer.stop()

        _measurementArray = np.vstack(self.workingArray)
        self.updateGraphSignal.emit(_measurementArray)

        self.workingArray = []
        self.sendConsoleUpdateSignal.emit("Sweep Data Finalised")
    
    @pyqtSlot()
    def sendUpdateGraphSignal(self):
        # It is possible for sendUpdateGraphSignal() to be queued by the self.timer.timeout event AS finaliseArray() is running, resulting the working array being cleared before sendUpdateGraphSignal() runs.
        # We can never be sure there isn't a signal emission already in the event queue waiting to be processed which will call a method to access self.workingArray AFTER it has been cleared by finaliseArray().
        # Hence, we check if there is valid data to display, before sending it to the Main GUI Thread.
        if self.workingArray:
            _workingArray = np.vstack(self.workingArray)
            self.updateGraphSignal.emit(_workingArray)



class analysisHandler(QObject):
    def __init__(self):
        super().__init__()
        self.cellArea = 0
        self.PowerIn = 0
    
    @pyqtSlot(np.ndarray)
    def updateAnalysisValues(self):
        pass



class MainWindow(QMainWindow):
    startSweepMeasurementSignal = pyqtSignal(np.ndarray)

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

        # Measurement Handler to Data Handler:
        self.measurementHandler.sendSweepPointSignal.connect(self.dataHandler.buildArrayFromSweepPoints, Qt.QueuedConnection)
        self.measurementHandler.measurementSweepFinishedSignal.connect(self.dataHandler.finaliseArray, Qt.QueuedConnection)

        # Measurement Handler to Main GUI Thread
        self.measurementHandler.sendVocValueSignal.connect(self.updateVocValue, Qt.QueuedConnection)
        self.measurementHandler.measurementSweepStartedSingal.connect(self.respondMeausurementStarted, Qt.QueuedConnection)
        self.measurementHandler.measurementSweepFinishedSignal.connect(self.respondForMeasurementFinished, Qt.QueuedConnection)
        self.measurementHandler.measurementVOCStartedSignal.connect(self.respondMeausurementStarted, Qt.QueuedConnection)
        self.measurementHandler.measurementVOCStartedSignal.connect(self.respondForMeasurementFinished, Qt.QueuedConnection)

        # Data Handler to Main GUI Thread
        self.dataHandler.updateGraphSignal.connect(self.plotData, Qt.QueuedConnection)

        # Main GUI Self Connections
        self.controlStartButton.clicked.connect(self.gatekeeperSweepMeasurement, Qt.QueuedConnection)
        self.controlMeasureVoc.clicked.connect(self.measurementHandler.measureVOC, Qt.QueuedConnection)
        self.inputFetchFolderPath.clicked.connect(self.folderBrowse, Qt.QueuedConnection)
        self.inputCellArea.valueChanged.connect(self.gatekeeperAnalysisVariables, Qt.QueuedConnection)
        self.inputPower.valueChanged.connect(self.gatekeeperAnalysisVariables, Qt.QueuedConnection)

        # Main GUI to Measurement Handler
        self.startSweepMeasurementSignal.connect(self.measurementHandler.measureSweep, Qt.QueuedConnection)

        # Console Connections
        self.measurementHandler.sendConsoleUpdateSignal.connect(self.updateConsole, Qt.QueuedConnection)
        self.dataHandler.sendConsoleUpdateSignal.connect(self.updateConsole, Qt.QueuedConnection)

    def createInstrumentSettings(self):

        self.InstrumentSettings = QGroupBox("Instrument Settings")
        self.layoutInstrumentSettings = QGridLayout(self.InstrumentSettings)

        self.labelFourOrTwoWire = QLabel("Terminal Settings", self.InstrumentSettings)
        self.inputFourOrTwoWire = QComboBox(self.InstrumentSettings)
        self.inputFourOrTwoWire.addItem("Four Wire")
        self.inputFourOrTwoWire.addItem("Two Wire")

        self.labelFrontOrRearPanel = QLabel("Panel Settings", self.InstrumentSettings)
        self.inputFrontOrRearPanel = QComboBox(self.InstrumentSettings)
        self.inputFrontOrRearPanel.addItem("Front Banana Connection")
        self.inputFrontOrRearPanel.addItem("Rear Triaxial Connection")

        self.layoutInstrumentSettings.addWidget(self.labelFourOrTwoWire, 0, 0)
        self.layoutInstrumentSettings.addWidget(self.inputFourOrTwoWire, 1, 0)
        self.layoutInstrumentSettings.addWidget(self.labelFrontOrRearPanel, 0, 1)
        self.layoutInstrumentSettings.addWidget(self.inputFrontOrRearPanel, 1, 1)

    def createSweepSettings(self):

        self.SweepSettings = QGroupBox("Sweep Settings")
        self.SweepSettings.setMaximumWidth(200)
        self.SweepSettings.setMaximumHeight(207) # Minimum height of QGroupBox, considering the space needed for it's child widgets
        self.layoutSweepSettings = QVBoxLayout(self.SweepSettings)

        self.labelStartVoltage = QLabel("Start Voltage (V)", self.SweepSettings)
        self.inputStartVoltage = QDoubleSpinBox(self.SweepSettings)
        self.inputStartVoltage.setSingleStep(0.01)
        self.inputStartVoltage.setRange(-10, 10)
        self.inputStartVoltage.setValue(1.05)

        self.labelEndVoltage = QLabel("End Voltage (V)", self.SweepSettings)
        self.inputEndVoltage = QDoubleSpinBox(self.SweepSettings)
        self.inputEndVoltage.setSingleStep(0.01)
        self.inputEndVoltage.setRange(-10, 10)
        self.inputEndVoltage.setValue(-0.05)

        self.labelScanRate = QLabel("Scan Rate (mV/s)", self.SweepSettings)
        self.inputScanRate = QDoubleSpinBox(self.SweepSettings)
        self.inputScanRate.setSingleStep(0.01)
        self.inputScanRate.setMinimum(0)
        self.inputScanRate.setValue(2000)

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

        self.layoutMeasurementControls.addWidget(self.controlStartButton)
        self.layoutMeasurementControls.addWidget(self.controlsStopButton)
        self.layoutMeasurementControls.addWidget(self.controlMeasureVoc)
        self.layoutMeasurementControls.addWidget(self.labelVocValue)
    
    def createDataDisplayTab(self):
 
        # Graph Tab Layout
        self.graphTab = QWidget()
        layoutGraphTab = QVBoxLayout(self.graphTab)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layoutGraphTab.addWidget(self.canvas)

        # Console Tab Layout
        self.consoleTab = QWidget()
        self.layoutConsoleTab = QVBoxLayout(self.consoleTab)
        self.console = QPlainTextEdit(self.consoleTab)
        self.console.setReadOnly(True)
        self.layoutConsoleTab.addWidget(self.console)

        # Tab layout (with graph and console)
        self.tabControl = QTabWidget()
        self.tabControl.addTab(self.graphTab, "Graph")
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

    @pyqtSlot()
    def respondMeausurementStarted(self):
        self.isMeasuring = True
        self.statusBar().showMessage("Measuring JV sweep...")
 
        # Measurement control buttons
        self.controlStartButton.setEnabled(False)
        self.controlMeasureVoc.setEnabled(False)
        
        # Analysis variables
        self.inputCellArea.setEnabled(False)
        self.inputCellName.setEnabled(False)

        # Sweep settings
        self.inputStartVoltage.setEnabled(False)
        self.inputEndVoltage.setEnabled(False)
        self.inputScanRate.setEnabled(False)
        self.inputSweepType.setEnabled(False)

        # Folder I/O setting
        self.inputFetchFolderPath.setEnabled(False)
        self.inputCellName.setEnabled(False)
    
    
    @pyqtSlot()
    def respondForMeasurementFinished(self):
        self.isMeasuring = False
        self.statusBar().showMessage("Measurement finished, ready to measure.")
        
        # Measurement control buttons
        self.controlStartButton.setEnabled(True)
        self.controlMeasureVoc.setEnabled(True)
        
        # Analysis variables
        self.inputCellArea.setEnabled(True)
        self.inputCellName.setEnabled(True)

        # Sweep settings
        self.inputStartVoltage.setEnabled(True)
        self.inputEndVoltage.setEnabled(True)
        self.inputScanRate.setEnabled(True)
        self.inputSweepType.setEnabled(True)

        # Folder I/O setting
        self.inputFetchFolderPath.setEnabled(True)
        self.inputCellName.setEnabled(True)
    
    
    @pyqtSlot(str)
    def updateConsole(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}]:\n{message}\n"
        self.console.appendPlainText(formatted_message)

    @pyqtSlot(float)
    def updateVocValue(self, value):
        print(self.displayWorkingFolderPath.height())
        self.valueVoc = value * 1000
        self.labelVocValue.setText(f"Voc: {self.valueVoc:.0f} mV")

    @pyqtSlot(np.ndarray)
    def plotData(self, dataToPlot):
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        ax.plot(dataToPlot[:,0], dataToPlot[:,1], "kx-")
        ax.grid()
        self.canvas.draw()

    @pyqtSlot()    
    def shutdown(self):
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

        if self.workingFolderPath:
            _startVoltage = self.inputStartVoltage.value() 
            _endVoltage =  self.inputEndVoltage.value()
            _scanRate = self.inputScanRate.value()
            _sweepProperties = np.empty([1, 3])
            _sweepProperties[0, :] = [_startVoltage, _endVoltage, _scanRate]

            self.startSweepMeasurementSignal.emit(_sweepProperties)
        else:
            self.AlertBox = QMessageBox()
            self.AlertBox.setWindowTitle("Warning!")
            self.AlertBox.setText("The working folder path not selected! A working folder path must be set before starting a measurement!")
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