from PyQt5.QtWidgets import *

app = QApplication([])
window = QWidget()

button1 = QPushButton('Hello')
button2 = QPushButton('World')

buttonElements = QVBoxLayout()
buttonElements.addWidget(button1)
buttonElements.addWidget(button2)

window.setLayout(buttonElements)

def on_element_clicked():
    alert = QMessageBox()
    alert.setText('Nice!')
    alert.exec()

button1.clicked.connect(on_element_clicked)
button2.clicked.connect(on_element_clicked)

window.show()
app.exec()