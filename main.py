import sys
import os
import xlrd

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTableWidgetItem
from main_ui import *
from threading import Thread
import json
import time


class MyWidget(QWidget):
    # 无参数的信号
    Signal_NoParameters = pyqtSignal()
    # 带一个参数(整数)的信号
    Signal_OneParameter = pyqtSignal(int)
    # 带一个参数(整数或者字符串)的重载版本的信号
    Signal_OneParameter_Overload = pyqtSignal([int], [str])
    # 带两个参数(整数,字符串)的信号
    Signal_TwoParameters = pyqtSignal(int, str)
    # 带两个参数([整数,整数]或者[整数,字符串])的重载版本的信号
    Signal_TwoParameters_Overload = pyqtSignal([int, int], [int, str])
    # 打开cookies文件后读取文件传输信号
    signal_cookies_opened = pyqtSignal(int, int, str)


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        self.widget = MyWidget()
        self.widget.signal_cookies_opened.connect(self.show_ui_cookies)
        self.toolButton.clicked.connect(self.open_file)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(['cookies', '用户', '状态'])

    def open_file(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                   "xls Files(*.xls)")
        print('打开的文件路径', fileName)

        thread = Thread(target=self.t_open_file, args=(fileName,))
        thread.start()

    def t_open_file(self, file):
        data = xlrd.open_workbook(file)
        table = data.sheet_by_index(0)
        cookies_list = []
        for rowNum in range(table.nrows):
            rowVale = table.row_values(rowNum)
            self.widget.signal_cookies_opened.emit(table.nrows, rowNum, rowVale[1])
            time.sleep(1)

    def show_ui_cookies(self, total, index, data):
        self.tableWidget.setRowCount(total)
        item = QTableWidgetItem(data)
        self.tableWidget.setItem(index, 0, item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWindow()
    myWin.show()
    sys.exit(app.exec_())
