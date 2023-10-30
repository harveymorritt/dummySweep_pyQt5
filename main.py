import sys
import random
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class TaskWaitForTenSeconds(QRunnable):
    @pyqtSlot()
    def run(self):
        print("Waiting")
        time.sleep(2)
        global DATA
        DATA = 10

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

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        self.createSweepSettings()
        self.createMeasurementSettings()
        self.createMeasurementControls()

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.SweepSettings, 0, 0)
        mainLayout.addWidget(self.MeasurementSettings, 0, 1)
        mainLayout.addWidget(self.MeasurementControls, 1, 0, 1, 2)
        mainLayout.addWidget(self.canvas, 0, 2, 2, 2)

        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)

        self.setCentralWidget(mainWidget)

        self.show()

    def createSweepSettings(self):

        self.SweepSettings = QGroupBox("Sweep Settings")
        self.SweepSettings.setMaximumWidth(150)

        labelStartVoltage = QLabel("Start Voltage (V)")
        inputStartVoltage = QDoubleSpinBox()
        inputStartVoltage.setSingleStep(0.01)
        inputStartVoltage.setRange(-10, 10)

        labelEndVoltage = QLabel("End Voltage (V)")
        inputEndVoltage = QDoubleSpinBox()
        inputEndVoltage.setSingleStep(0.01)
        inputEndVoltage.setRange(-10, 10)

        labelScanRate = QLabel("Scan Rate (mV/s)")
        inputScanRate = QDoubleSpinBox()
        inputScanRate.setSingleStep(0.01)
        inputScanRate.setMinimum(0)

        labelSweepType = QLabel("Sweep Type")
        inputSweepType = QComboBox()
        inputSweepType.addItem("Linear")
        inputSweepType.addItem("Reverse")
        inputSweepType.addItem("Symmetric")

        layoutSweepSettings = QVBoxLayout()
        layoutSweepSettings.addWidget(labelStartVoltage)
        layoutSweepSettings.addWidget(inputStartVoltage)
        layoutSweepSettings.addWidget(labelEndVoltage)
        layoutSweepSettings.addWidget(inputEndVoltage)
        layoutSweepSettings.addWidget(labelScanRate)
        layoutSweepSettings.addWidget(inputScanRate)
        layoutSweepSettings.addWidget(labelSweepType)
        layoutSweepSettings.addWidget(inputSweepType)
        layoutSweepSettings.addStretch()
            
        self.SweepSettings.setLayout(layoutSweepSettings)

    def createMeasurementSettings(self):

        self.MeasurementSettings = QGroupBox("Measurement Settings")
        self.MeasurementSettings.setMaximumWidth(150)

        labelCellArea = QLabel("Cell Area (cm2)")
        inputCellArea = QDoubleSpinBox()
        inputCellArea.setSingleStep(0.01)
        inputCellArea.setMinimum(0)

        labelPower = QLabel("Light Intensity (units)")
        inputPower = QDoubleSpinBox()
        inputPower.setSingleStep(0.01)
        inputPower.setMinimum(0)

        layoutMeasurementSettings = QVBoxLayout()
        layoutMeasurementSettings.addWidget(labelCellArea)
        layoutMeasurementSettings.addWidget(inputCellArea)
        layoutMeasurementSettings.addWidget(labelPower)
        layoutMeasurementSettings.addWidget(inputPower)
        layoutMeasurementSettings.addStretch()

        self.MeasurementSettings.setLayout(layoutMeasurementSettings)

    def createMeasurementControls(self):

        self.MeasurementControls = QGroupBox()
        
        controlStartButton = QPushButton("Start Measurement")
        controlStartButton.clicked.connect(self.plotData)

        controlMeasureVoc = QPushButton("10 Second Wait")
        controlMeasureVoc.clicked.connect(self.waitForTenSeconds)

        layoutMeasurementControls = QHBoxLayout()
        layoutMeasurementControls.addWidget(controlStartButton)
        layoutMeasurementControls.addWidget(controlMeasureVoc)

        self.MeasurementControls.setLayout(layoutMeasurementControls)

    def plotData(self):
        global DATA
        print(DATA)

        data = [random.random() for i in range(10)]

        ax = self.figure.add_subplot(111)
        ax.clear()
        ax.plot(data, "*-")
        self.canvas.draw()

    def waitForTenSeconds(self):
        task = TaskWaitForTenSeconds()
        self.threadpool.start(task)


def main():

    ### Global variables ###
    global DATA
    DATA = 2

    app = QApplication(sys.argv)
    window = MainWindow()
    app.exec()

main()