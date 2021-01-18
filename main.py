import sys
import os

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow
from main_ui import *


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        self.toolButton.clicked.connect(self.open_file)
        self.model = QStandardItemModel(4, 4)  # 存储任意结构数据
        self.model.setHorizontalHeaderLabels(['序号', '状态','cookies'])
        self.tableView.setModel(self.model)

    def open_file(self):
        fileName,fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
        "All Files(*);;Text Files(*.txt)")
        print('打开的文件路径',fileName)

    def show_cookies(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWindow()
    myWin.show()
    sys.exit(app.exec_())
