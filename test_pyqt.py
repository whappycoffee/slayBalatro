from PyQt6.QtWidgets import QApplication, QLabel
import sys

app = QApplication(sys.argv)
label = QLabel("PyQt6 is working!")
label.show()
sys.exit(app.exec()) 