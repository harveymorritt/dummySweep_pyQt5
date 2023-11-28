import time
import numpy as np
from PyQt5.QtCore import *

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
        
        self.validState = True
        self.measurementValid = True
        self.measurementConsent = False

        self.sendConsoleUpdateSignal.emit("Keithley 2450 Initilised")

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
        _repeats = int(_sweepSettings[0, 2])
        _scanRate = _sweepSettings[0, 3]
        
        _n = 1.5
        _k = 1.38e-23
        _T = 300
        _I0 = 1e-12
        _q = 1.6e-19

        if self.measurementValid:
            self.measurementConsent = True
            self.sweepSetStartedSingal.emit()
            
            for _sweepNumber in range(1, _repeats+1):
                
                # Only send messages if measurement has consent
                if self.measurementConsent:
                    _consoleMessage = f"Measuring Sweep ({_sweepNumber} of {_repeats})"
                    self.sendConsoleUpdateSignal.emit(_consoleMessage)
                    self.sendStatusUpdateSignal.emit(_consoleMessage)
                
                _sweepPoint = np.empty((1, 2))
                
                _yAxisShift = np.round(0.05+((0.25-0.05)*np.random.rand()), 3)
                _measurementPoints = np.linspace(_startVoltage, _endVoltage, num=250)

                for _voltagePoint in _measurementPoints:
                    
                    if self.measurementConsent:

                        _sleepTime = 0.045+(0.055-0.045)*np.random.rand()
                        time.sleep(_sleepTime)

                        _current = _I0*(np.exp((_q * _voltagePoint)/(_n*_k*_T)) - 1)

                        _currentError = -0.005+(0.015+0.005)*np.random.rand()

                        _sweepPoint[0, 0] = _voltagePoint
                        _sweepPoint[0, 1] = _current - _yAxisShift + _currentError
                        
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