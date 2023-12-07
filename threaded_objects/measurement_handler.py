import time
import numpy as np
from PyQt5.QtCore import *

from .instruments import dummyInstrument as inst

class MeasurementHandler(QObject):
    sendVocValueSignal = pyqtSignal(float)
    sendSweepPointSignal = pyqtSignal(np.ndarray)
    
    sweepSetStartedSingal = pyqtSignal()     # Measurement is active.
    finaliseSweepArraySignal = pyqtSignal()  # A sweep has finished, array can be sent for analysis.
    sweepSetFinishedSignal = pyqtSignal()    # Measurement is no longer active.
    abortMeasurementSignal = pyqtSignal()    # When the sweep has been aborted succesfully
    
    measurementVOCStartedSignal = pyqtSignal()
    measurementVOCFinishedSignal = pyqtSignal()
    sendConsoleUpdateSignal = pyqtSignal(str)
    sendStatusUpdateSignal = pyqtSignal(str)

    def __init__(self, mutexMeasurement):
        super().__init__()
        self.mutexMeasurement = mutexMeasurement
        
        _initilised, _message = inst.initilise()

        if _initilised:
            self.validState = True
            self.measurementConsent = False

            self.sendConsoleUpdateSignal.emit(_message)
        else:
            self.validState = False
            self.measurementConsent = False
        
            self.sendConsoleUpdateSignal.emit(_message)

    @pyqtSlot()
    def abortMeasurement(self):
        self.measurementConsent = False

        self.sendConsoleUpdateSignal.emit("Sweep Abort Command Registered")
        self.sendStatusUpdateSignal.emit("Aborting Measurement...")

    @pyqtSlot()
    def measureVOC(self):
        self.sendConsoleUpdateSignal.emit("Voc Measurement Started")
        self.measurementVOCStartedSignal.emit()
        if self.validState:
            _dataPoint = inst.measureVOC()
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
        _repeats = int(_sweepSettings[0, 2])
        _scanRate = _sweepSettings[0, 3]
        
        if self.validState:
            self.measurementConsent = True
            self.sweepSetStartedSingal.emit()
            
            for _sweepNumber in range(1, _repeats+1):
                
                # Only send messages if measurement has consent
                if self.measurementConsent:
                    _consoleMessage = f"Measuring Sweep ({_sweepNumber} of {_repeats})"
                    self.sendConsoleUpdateSignal.emit(_consoleMessage)
                    self.sendStatusUpdateSignal.emit(_consoleMessage)
                
                _sweepPoint = np.empty((1, 2))
                
                _measurementPoints = np.linspace(_startVoltage, _endVoltage, num=250)

                for _voltagePoint in _measurementPoints:
                    
                    if self.measurementConsent:

                        _voltage, _current = inst.measurePoint(_voltagePoint)

                        _sweepPoint[0, 0] = _voltage
                        _sweepPoint[0, 1] = _current
                        
                        self.sendSweepPointSignal.emit(_sweepPoint.copy()) # .copy() otherwise the for loop "catches up" with the emit signal, and you end up writing over the data being emitted.    
                                
                # Only send finaliseSweepArraySignal IF the program finished the loop with measurement consent
                if self.measurementConsent: 
                    self.sendConsoleUpdateSignal.emit(f"Sweep Finished ({_sweepNumber} of {_repeats})")
                    self.finaliseSweepArraySignal.emit()
            
            # Only send measurement finished if there is measurement consent
            if self.measurementConsent:
                self.sweepSetFinishedSignal.emit()
            else:
                self.abortMeasurementSignal.emit()
        
        else:
            pass
            # message about not in valid state
        self.mutexMeasurement.unlock()