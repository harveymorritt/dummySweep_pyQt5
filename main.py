import sys
import random
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class TaskWaitForTwoSeconds(QRunnable):
    @pyqtSlot()
    def run(self):
        print("Waiting")
        time.sleep(2)

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

        # Setting up figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Sub-widgets
        self.createSweepSettings()
        self.createMeasurementSettings()
        self.createMeasurementControls()

        # Connections
        self.controlStartButton.clicked.connect(self.plotData)
        self.controlMeasureVoc.clicked.connect(self.waitForTenSeconds)

        # Main layout
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.SweepSettings, 0, 0)
        mainLayout.addWidget(self.MeasurementSettings, 0, 1)
        mainLayout.addWidget(self.MeasurementControls, 1, 0, 1, 2)
        mainLayout.addWidget(self.canvas, 0, 2, 2, 2)

        # Building and showing main widget
        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)
        self.show()

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
        self.controlMeasureVoc = QPushButton("10 Second Wait")

        self.layoutMeasurementControls = QHBoxLayout()
        self.layoutMeasurementControls.addWidget(self.controlStartButton)
        self.layoutMeasurementControls.addWidget(self.controlMeasureVoc)

        self.MeasurementControls.setLayout(self.layoutMeasurementControls)

    def plotData(self):

        data = [random.random() for i in range(10)]

        ax = self.figure.add_subplot(111)
        ax.clear()
        ax.plot(data, "*-")
        self.canvas.draw()

    def waitForTenSeconds(self):
        task = TaskWaitForTwoSeconds()
        self.threadpool.start(task)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    app.exec()

main()