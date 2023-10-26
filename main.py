import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Dummy JV")
        
        button1 = QPushButton("Hello world!")
        button1.setCheckable(True)
        button1.clicked.connect(self.buttonPressed)
        
        self.setCentralWidget(button1)
    
    def buttonPressed(self):
        alert = QMessageBox()
        alert.setText('Nice!')
        alert.setWindowTitle('Alert!')
        alert.exec()

app = QApplication(sys.argv)

window = mainWindow()
window.show()

app.exec()