import re
import os
import numpy as np
from PyQt5.QtCore import *

class DataSaver(QRunnable):
    def __init__(self, mutex, dataArray, sweepSettings, analysisSettings, cellName, dataSavePath):
        super().__init__()
        self.mutexFileSaving = mutex

        self.dataArray = dataArray
        self.sweepSettings = sweepSettings
        self.analysisSettings = analysisSettings
        self.cellName = cellName
        self.dataSavePath = dataSavePath

        self.startVoltage = self.sweepSettings[0, 0]
        self.endVoltage = self.sweepSettings[0, 1]
        self.scanRate = self.sweepSettings[0, 2]

        self.cellArea = self.analysisSettings[0, 0]
        self.power = self.analysisSettings[0, 1]

        if not self.cellName:
            self.cellName = "DEFAULT"

    def run(self):

        self.mutexFileSaving.lock() # Theoretically possible for multiple DataSaver QRunnables to operate at once, to prevent duplicate increments and therefore file overwrites, use a mutex

        _header = f"Sweep Settings:\nStart Voltage (V): {self.startVoltage}\nEnd Voltage (V): {self.endVoltage}\nScan Rate (mV/s): {self.scanRate}\n\nAnalysis Variables:\nCell Area(cm2): {self.cellArea}\nPower (mWcm-2): {self.power}\n\nVoltage(V)   Current (A)"
        _cellName = self.cellName

        _pattern = re.compile(rf"{re.escape(_cellName)}(?:_(\d+))?.*$")
        _workingFolderPath = self.dataSavePath

        # Check if files saved with same name
        _highestNumFound = 0
        for _fileName in os.listdir(_workingFolderPath):
            _match = _pattern.match(_fileName)

            # If files with same name, check for number
            if _match:
                _matchedNumber = _match.group(1)

                # If it has a number, keep track of the highest number found
                if _matchedNumber:
                    _num = int(_matchedNumber)
                    _highestNumFound = max(_highestNumFound, _num)
        
        # If no number found, save file as "file number 1", otherwise increment
        if _highestNumFound == 0:
            _cellName = _cellName + "_1"
        else:
            _nextNum = _highestNumFound + 1
            _cellName = _cellName + "_" + str(_nextNum)

        _path = self.dataSavePath+f"\\{_cellName}.csv"
        np.savetxt(_path, self.dataArray, delimiter='   ', header=_header, comments='', fmt='%.5e')

        self.mutexFileSaving.unlock()