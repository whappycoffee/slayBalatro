from PySide6.QtWidgets import QApplication, QLabel
import sys

app = QApplication(sys.argv)
label = QLabel("PySide6 is working!")
label.show()
app.exec() 