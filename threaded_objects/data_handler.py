import numpy as np
from PyQt5.QtCore import *

class DataHandler(QObject):
    updateGraphSignal = pyqtSignal(np.ndarray)
    sendConsoleUpdateSignal = pyqtSignal(str)
    sendStatusUpdateSignal = pyqtSignal(str)
    sendDataArrayForSavingSingal = pyqtSignal(np.ndarray)

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
        self.sendDataArrayForSavingSingal.emit(_measurementArray)

        self.workingArray = []
        self.sendConsoleUpdateSignal.emit("Sweep Data Finalised")
    
    @pyqtSlot()
    def abortMeasurement(self):
        self.workingArray = []

        # The console and status are updated from "aborting" to "aborted" ONLY once the measurement thread has cleared the working array, which only happens if the main sweep loop in the meausrement thread is exited.
        self.sendConsoleUpdateSignal.emit("Measurement Aborted Successfully")
        self.sendStatusUpdateSignal.emit("Measurement Aborted. Ready to measure.")

    @pyqtSlot()
    def sendUpdateGraphSignal(self):
        # It is possible for sendUpdateGraphSignal() to be queued by the self.timer.timeout event AS finaliseArray() is running, resulting the working array being cleared before sendUpdateGraphSignal() runs.
        # We can never be sure there isn't a signal emission already in the event queue waiting to be processed which will call a method to access self.workingArray AFTER it has been cleared by finaliseArray().
        # Hence, we check if there is valid data to display, before sending it to the Main GUI Thread.
        if self.workingArray:
            _workingArray = np.vstack(self.workingArray)
            self.updateGraphSignal.emit(_workingArray)
