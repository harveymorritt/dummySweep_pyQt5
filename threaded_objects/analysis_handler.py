import numpy as np
from PyQt5.QtCore import *

class AnalysisHandler(QObject):
    def __init__(self):
        super().__init__()
        self.cellArea = 0
        self.PowerIn = 0
    
    @pyqtSlot(np.ndarray)
    def updateAnalysisValues(self):
        pass