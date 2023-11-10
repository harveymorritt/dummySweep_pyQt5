import sys
import random
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
from numpy import *
from datetime import datetime

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class TaskWaitForTwoSeconds(QRunnable):
    @pyqtSlot()
    def run(self):
        print("Waiting")
        time.sleep(2)

class MeasurementHandler(QObject):
    sendVocValue = pyqtSignal(float)
    sendSweepPoint = pyqtSignal(ndarray)
    measurementSweepStarted = pyqtSignal()
    measurementSweepFinished = pyqtSignal()
    measurementVOCStarted = pyqtSignal()
    measurementVOCFinished = pyqtSignal()
    sendConsoleUpdateSignal = pyqtSignal(str)

    def __init__(self, mutexMeasurement):
        super().__init__()
        self.mutexMeasurement = mutexMeasurement
        self.validState = True
        self.measurementValid = True

    @pyqtSlot()
    def measureVOC(self):
        self.measurementVOCStarted.emit()
        if self.validState:
            _dataPoint = random.rand()
            self.sendVocValue.emit(_dataPoint)
        else:
            pass
            ### Return message measurement not being valid ###
        self.measurementVOCFinished.emit()
        self.sendConsoleUpdateSignal.emit(f"Voc Measurement Completed\nValue: {_dataPoint:.3f} V")

    def measureSweep(self):
        self.measurementSweepStarted.emit()
        self.mutexMeasurement.lock()
        
        if self.measurementValid:
            _sweepPoint = empty((1, 2))
            for i in range (1, 101):
                time.sleep(0.02)
                _sweepPoint[0, 0] = i
                _sweepPoint[0, 1] = i * (1 + ((1-random.rand()*2))*0.1)
                print(_sweepPoint[0])
                self.sendSweepPoint.emit(_sweepPoint.copy()) # .copy() otherwise the for loop "catches up" with the emit signal, and you end up writing over the data being emitted.

        self.mutexMeasurement.unlock()
        self.measurementSweepFinished.emit()

class DataHandler(QObject):
    updateGraph = pyqtSignal(ndarray)

    def __init__(self):
        super().__init__()
        
        self.workingArray = []

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sendUpdateGraphSignal, Qt.QueuedConnection)

    @pyqtSlot(ndarray)
    def buildArrayFromSweepPoints(self, receivedSweepPoint):
        if not self.timer.isActive():
            self.timer.start(333)
        
        self.workingArray.append(receivedSweepPoint)
    
    @pyqtSlot()
    def finaliseArray(self):
        self.timer.stop()

        _measurementArray = vstack(self.workingArray)
        self.updateGraph.emit(_measurementArray)

        self.workingArray = []
    
    @pyqtSlot()
    def sendUpdateGraphSignal(self):
        # It is possible for sendUpdateGraphSignal() to be queued by the self.timer.timeout event AS finaliseArray() is running, resulting the working array being cleared before sendUpdateGraphSignal() runs.
        # We can never be sure there isn't a signal emission already in the event queue waiting to be processed which will call a method to access self.workingArray AFTER it has been cleared by finaliseArray().
        # Hence, we check if there is valid data to display, before sending it to the Main GUI Thread.
        if self.workingArray:
            _workingArray = vstack(self.workingArray)
            self.updateGraph.emit(_workingArray)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dummy JV")

        self.threadpool = QThreadPool()

        # Warning if only one thread (will probably never happen but who knows what people will try to run this on)
        if self.threadpool.maxThreadCount() == 1: 
            warningThreads = QMessageBox()
            warningThreads.setWindowTitle("Warning!")
            warningThreads.setText("You are running this program on a machine with only 1 thread! This program makes use of mulithreading, please run on a machine with at least 2 threads or unexpected behaviour may occur!")
            warningThreads.exec_()

        # Sub-widgets
        self.createSweepSettings()
        self.createMeasurementSettings()
        self.createMeasurementControls()

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
        self.measurementHandler.sendSweepPoint.connect(self.dataHandler.buildArrayFromSweepPoints, Qt.QueuedConnection)
        self.measurementHandler.measurementSweepFinished.connect(self.dataHandler.finaliseArray, Qt.QueuedConnection)

        # Measurement Handler to Main GUI Thread
        self.measurementHandler.sendVocValue.connect(self.updateVocValue, Qt.QueuedConnection)
        self.measurementHandler.measurementSweepStarted.connect(self.disableStartMeasurementButtons, Qt.QueuedConnection)
        self.measurementHandler.measurementSweepFinished.connect(self.enableStartMeasurementButtons, Qt.QueuedConnection)
        self.measurementHandler.measurementVOCStarted.connect(self.disableStartMeasurementButtons, Qt.QueuedConnection)
        self.measurementHandler.measurementVOCStarted.connect(self.enableStartMeasurementButtons, Qt.QueuedConnection)
        self.measurementHandler.sendConsoleUpdateSignal.connect(self.updateConsole, Qt.QueuedConnection)

        # Data Handler to Main GUI Thread
        self.dataHandler.updateGraph.connect(self.plotData, Qt.QueuedConnection)

        # Main GUI Self Connections
        self.controlStartButton.clicked.connect(self.measurementHandler.measureSweep, Qt.QueuedConnection)
        self.controlMeasureVoc.clicked.connect(self.measurementHandler.measureVOC, Qt.QueuedConnection) 

    def createSweepSettings(self):

        self.SweepSettings = QGroupBox("Sweep Settings")
        self.SweepSettings.setMaximumWidth(150)

        self.labelStartVoltage = QLabel("Start Voltage (V)")
        self.inputStartVoltage = QDoubleSpinBox()
        self.inputStartVoltage.setSingleStep(0.01)
        self.inputStartVoltage.setRange(-10, 10)

        self.labelEndVoltage = QLabel("End Voltage (V)")
        self.inputEndVoltage = QDoubleSpinBox()
        self.inputEndVoltage.setSingleStep(0.01)
        self.inputEndVoltage.setRange(-10, 10)

        self.labelScanRate = QLabel("Scan Rate (mV/s)")
        self.inputScanRate = QDoubleSpinBox()
        self.inputScanRate.setSingleStep(0.01)
        self.inputScanRate.setMinimum(0)

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

    @pyqtSlot(float)
    def updateVocValue(self, value):
        self.valueVoc = value * 1000
        self.labelVocValue.setText(f"Voc: {self.valueVoc:.0f} mV")

    @pyqtSlot(ndarray)
    def plotData(self, dataToPlot):
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        ax.plot(dataToPlot[:,0], dataToPlot[:,1], "*-")
        self.canvas.draw()

    @pyqtSlot()    
    def shutdown(self):
        self.THREAD_Measurement.quit()
        self.THREAD_Measurement.wait()
        self.THREAD_Data.quit()
        self.THREAD_Data.wait()
    
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

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    app.aboutToQuit.connect(window.shutdown)
    app.exec()

main()