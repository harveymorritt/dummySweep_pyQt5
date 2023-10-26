import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class mainWindow(QWidget):
    def __init__(self):
        super().__init__()
                
        self.setWindowTitle("Dummy JV")
        
        self.createSweepSettings()
        self.createMeasurementSettings()

        inputStartButton = QPushButton("Start Measurement")

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.SweepSettings)
        mainLayout.addWidget(self.MeasurementSettings)
        mainLayout.addWidget(inputStartButton)

        self.setLayout(mainLayout)

        self.show()

    def createSweepSettings(self):

        self.SweepSettings = QGroupBox("Sweep Settings")

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
        layoutSweepSettings.addStretch()
        layoutSweepSettings.addWidget(labelEndVoltage)
        layoutSweepSettings.addWidget(inputEndVoltage)
        layoutSweepSettings.addStretch()
        layoutSweepSettings.addWidget(labelScanRate)
        layoutSweepSettings.addWidget(inputScanRate)
        layoutSweepSettings.addStretch()
        layoutSweepSettings.addWidget(labelSweepType)
        layoutSweepSettings.addWidget(inputSweepType)
            
        self.SweepSettings.setLayout(layoutSweepSettings)

    def createMeasurementSettings(self):

        self.MeasurementSettings = QGroupBox("Measurement Settings")

        labelCellArea = QLabel("Cell Area (cm2)")
        inputCellArea = QDoubleSpinBox()
        inputCellArea.setSingleStep(0.01)
        inputCellArea.setMinimum(0)

        labelPower = QLabel("Light Intensity (units)")
        inputPower = QDoubleSpinBox()
        inputPower.setSingleStep(0.01)
        inputPower.setMinimum(0)

        layoutMeasurementSettings = QVBoxLayout()
        layoutMeasurementSettings.addStretch()
        layoutMeasurementSettings.addWidget(labelCellArea)
        layoutMeasurementSettings.addWidget(inputCellArea)
        layoutMeasurementSettings.addStretch()
        layoutMeasurementSettings.addWidget(labelPower)
        layoutMeasurementSettings.addWidget(inputPower)
        layoutMeasurementSettings.addStretch()

        self.MeasurementSettings.setLayout(layoutMeasurementSettings)
    
app = QApplication(sys.argv)
window = mainWindow()

app.exec()