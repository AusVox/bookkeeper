import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from bookkeeper.presenter.presenter import Presenter




app = QApplication(sys.argv)
window = QMainWindow()
layout = QVBoxLayout()
test = Presenter()
layout.addWidget(test.tree_widget)
widget = QWidget()
widget.setLayout(layout)
window.setCentralWidget(widget)
window.show()
sys.exit(app.exec())