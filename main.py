import sys
import random
import time

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
        self.sendConsoleUpdateSignal.emit("Sweep Measurement Started")
        self.measurementSweepStartedSingal.emit()
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
        
        else:
            pass
            # message about not in valid state
        self.mutexMeasurement.unlock()
        self.measurementSweepFinishedSignal.emit()



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



class MainWindow(QMainWindow):
    startSweepMeasurement = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dummy JV")

        # Sub-widgets
        self.createSweepSettings()
        self.createMeasurementSettings()
        self.createMeasurementControls()
        self.createDataDisplayTab()

        # Main UI
        self.buildMainUI()

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
        self.measurementHandler.measurementSweepStartedSingal.connect(self.disableStartMeasurementButtons, Qt.QueuedConnection)
        self.measurementHandler.measurementSweepFinishedSignal.connect(self.enableStartMeasurementButtons, Qt.QueuedConnection)
        self.measurementHandler.measurementVOCStartedSignal.connect(self.disableStartMeasurementButtons, Qt.QueuedConnection)
        self.measurementHandler.measurementVOCStartedSignal.connect(self.enableStartMeasurementButtons, Qt.QueuedConnection)

        # Data Handler to Main GUI Thread
        self.dataHandler.updateGraphSignal.connect(self.plotData, Qt.QueuedConnection)

        # Main GUI Self Connections
        self.controlStartButton.clicked.connect(self.prepSweepMeasurement, Qt.QueuedConnection)
        self.controlMeasureVoc.clicked.connect(self.measurementHandler.measureVOC, Qt.QueuedConnection)

        # Main GUI to Measurement Handler
        self.startSweepMeasurement.connect(self.measurementHandler.measureSweep, Qt.QueuedConnection)

        # Console Connections
        self.measurementHandler.sendConsoleUpdateSignal.connect(self.updateConsole, Qt.QueuedConnection)
        self.dataHandler.sendConsoleUpdateSignal.connect(self.updateConsole, Qt.QueuedConnection)

    def createSweepSettings(self):

        self.SweepSettings = QGroupBox("Sweep Settings")
        self.SweepSettings.setMaximumWidth(150)

        self.labelStartVoltage = QLabel("Start Voltage (V)")
        self.inputStartVoltage = QDoubleSpinBox()
        self.inputStartVoltage.setSingleStep(0.01)
        self.inputStartVoltage.setRange(-10, 10)
        self.inputStartVoltage.setValue(1.05)

        self.labelEndVoltage = QLabel("End Voltage (V)")
        self.inputEndVoltage = QDoubleSpinBox()
        self.inputEndVoltage.setSingleStep(0.01)
        self.inputEndVoltage.setRange(-10, 10)
        self.inputEndVoltage.setValue(-0.05)

        self.labelScanRate = QLabel("Scan Rate (mV/s)")
        self.inputScanRate = QDoubleSpinBox()
        self.inputScanRate.setSingleStep(0.01)
        self.inputScanRate.setMinimum(0)
        self.inputScanRate.setValue(2000)

        self.labelSweepType = QLabel("Sweep Type")
        self.inputSweepType = QComboBox()
        self.inputSweepType.addItem("Linear")
        self.inputSweepType.addItem("Reverse")
        self.inputSweepType.addItem("Symmetric")

        self.layoutSweepSettings = QVBoxLayout()
        self.layoutSweepSettings.addWidget(self.labelStartVoltage)
        self.layoutSweepSettings.addWidget(self.inputStartVoltage)
        self.layoutSweepSettings.addWidget(self.labelEndVoltage)
        self.layoutSweepSettings.addWidget(self.inputEndVoltage)
        self.layoutSweepSettings.addWidget(self.labelScanRate)
        self.layoutSweepSettings.addWidget(self.inputScanRate)
        self.layoutSweepSettings.addWidget(self.labelSweepType)
        self.layoutSweepSettings.addWidget(self.inputSweepType)
        self.layoutSweepSettings.addStretch()
            
        self.SweepSettings.setLayout(self.layoutSweepSettings)

    def createMeasurementSettings(self):

        self.MeasurementSettings = QGroupBox("Measurement Settings")
        self.MeasurementSettings.setMaximumWidth(150)

        self.labelCellArea = QLabel("Cell Area (cm2)")
        self.inputCellArea = QDoubleSpinBox()
        self.inputCellArea.setSingleStep(0.01)
        self.inputCellArea.setMinimum(0)

        self.labelPower = QLabel("Light Intensity (units)")
        self.inputPower = QDoubleSpinBox()
        self.inputPower.setSingleStep(0.01)
        self.inputPower.setMinimum(0)

        self.layoutMeasurementSettings = QVBoxLayout()
        self.layoutMeasurementSettings.addWidget(self.labelCellArea)
        self.layoutMeasurementSettings.addWidget(self.inputCellArea)
        self.layoutMeasurementSettings.addWidget(self.labelPower)
        self.layoutMeasurementSettings.addWidget(self.inputPower)
        self.layoutMeasurementSettings.addStretch()

        self.MeasurementSettings.setLayout(self.layoutMeasurementSettings)

    def createMeasurementControls(self):

        self.MeasurementControls = QGroupBox()
        
        self.controlStartButton = QPushButton("Start Measurement")
        self.controlMeasureVoc = QPushButton("Measure Voc")
        self.labelVocValue = QLabel("Voc: NaN")

        self.layoutMeasurementControls = QHBoxLayout()
        self.layoutMeasurementControls.addWidget(self.controlStartButton)
        self.layoutMeasurementControls.addWidget(self.controlMeasureVoc)
        self.layoutMeasurementControls.addWidget(self.labelVocValue)

        self.MeasurementControls.setLayout(self.layoutMeasurementControls)
    
    def createDataDisplayTab(self):
 
        # Graph Tab Layout
        self.graphTab = QWidget()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        graphLayout = QVBoxLayout()
        graphLayout.addWidget(self.canvas)
        self.graphTab.setLayout(graphLayout)

        # Console Tab Layout
        self.consoleTab = QWidget()
        self.console = QPlainTextEdit(self.consoleTab)
        self.console.setReadOnly(True)
        self.consoleLayout = QVBoxLayout()
        self.consoleLayout.addWidget(self.console)
        self.consoleTab.setLayout(self.consoleLayout)

        # Tab layout (with graph and console)
        self.tabControl = QTabWidget()
        self.tabControl.addTab(self.graphTab, "Graph")
        self.tabControl.addTab(self.consoleTab, "Console")

    def buildMainUI(self):

        # Main layout
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.SweepSettings, 0, 0)
        mainLayout.addWidget(self.MeasurementSettings, 0, 1)
        mainLayout.addWidget(self.MeasurementControls, 1, 0, 1, 2)
        mainLayout.addWidget(self.tabControl, 0, 2, 2, 2)

        # Building and showing main widget
        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)
        self.show()

    @pyqtSlot()
    def disableStartMeasurementButtons(self):
        self.controlStartButton.setDisabled(True)
        self.controlMeasureVoc.setDisabled(True)
    
    @pyqtSlot()
    def enableStartMeasurementButtons(self):
        self.controlStartButton.setEnabled(True)
        self.controlMeasureVoc.setEnabled(True)
    
    @pyqtSlot(str)
    def updateConsole(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}]:\n{message}\n"
        self.console.appendPlainText(formatted_message)

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
        self.canvas.draw()

    @pyqtSlot()    
    def shutdown(self):
        self.THREAD_Measurement.quit()
        self.THREAD_Measurement.wait()
        self.THREAD_Data.quit()
        self.THREAD_Data.wait()
    
    @pyqtSlot()
    def prepSweepMeasurement(self):
        """ Packs the current sweep settings into an array and sends it to the measurement thread"""

        _startVoltage = self.inputStartVoltage.value() 
        _endVoltage =  self.inputEndVoltage.value()
        _scanRate = self.inputScanRate.value()
        _sweepProperties = np.empty([1, 3])
        _sweepProperties[0, :] = [_startVoltage, _endVoltage, _scanRate]

        self.startSweepMeasurement.emit(_sweepProperties)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    app.aboutToQuit.connect(window.shutdown)
    app.exec()

main()