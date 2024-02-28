
import sys
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QDialog
from out_window import Ui_OutputDialog

class Ui_Dialog(QDialog):
    def __init__(self):
        super(Ui_Dialog, self).__init__()
        loadUi("mainwindow.ui", self)

        self.runButton.clicked.connect(self.runSlot)

        self._new_window = None
        self.Videocapture_ = None

    def refreshAll(self):
        self.Videocapture_ = "0"  #Set the text of lineEdit once it's valid

    @pyqtSlot()
    def runSlot(self):
        print("Clicked Run")   #Called when the user presses the Run button
        self.refreshAll()
        print(self.Videocapture_)
        ui.hide()  # hide the main window
        self.outputWindow_()  # Create and open new output window

    def outputWindow_(self):
        self._new_window = Ui_OutputDialog() # Called when the user presses the Run button
        self._new_window.show()
        self._new_window.startVideo(self.Videocapture_)
        print("Video Played")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Ui_Dialog()
    ui.show()
    sys.exit(app.exec_())