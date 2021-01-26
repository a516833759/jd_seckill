import sys
import os
import xlrd

from PyQt5.QtCore import pyqtSignal, QDateTime
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTableWidgetItem, QMessageBox
from jd_main_ui import *
from threading import Thread
from jd_logger import logger
from utils.util import Dict
from jd_spider_requests import JdSeckill
import json
import time
import queue
import ctypes
import inspect
import asyncio

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    try:
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            # pass
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
    except Exception as err:
        print(err)


def stop_thread(thread):
    """终止线程"""
    _async_raise(thread.ident, SystemExit)

class MyWidget(QWidget):
    # 无参数的信号
    # Signal_NoParameters = pyqtSignal()
    # # 带一个参数(整数)的信号
    # Signal_OneParameter = pyqtSignal(int)
    # # 带一个参数(整数或者字符串)的重载版本的信号
    # Signal_OneParameter_Overload = pyqtSignal([int], [str])
    # # 带两个参数(整数,字符串)的信号
    # Signal_TwoParameters = pyqtSignal(int, str)
    # # 带两个参数([整数,整数]或者[整数,字符串])的重载版本的信号
    # Signal_TwoParameters_Overload = pyqtSignal([int, int], [int, str])
    # 打开cookies文件后读取文件传输信号
    signal_add_log = pyqtSignal(str, str, int)
    signal_cookies_opened = pyqtSignal(int, int, int, str)
    signal_login = pyqtSignal(str, str, int)


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        self.widget = MyWidget()
        self.widget.signal_cookies_opened.connect(self.show_ui_cookies)
        self.widget.signal_login.connect(self.update_widget)
        self.widget.signal_add_log.connect(self.update_widget)
        self.tableWidget.setColumnCount(8)
        self.tableWidget.setHorizontalHeaderLabels(['id', '用户', 'cookies', '登录状态', '订单号', '商品', '下单状态', '日志'])
        self.tableWidget.setColumnWidth(7,300)
        self.toolButton.clicked.connect(self.open_file)
        self.pushButton_4.clicked.connect(self.start)
        self.pushButton_6.clicked.connect(self.save_config)
        self.pushButton_7.clicked.connect(self.test_login)
        self.pushButton_5.clicked.connect(self.stop)
        self.load_config()
        self.queue = queue.Queue(maxsize=100)

    def open_file(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                   "xls Files(*.xls)")
        if not fileName:
            return
        thread = Thread(target=self.t_open_file, args=(fileName,))
        thread.start()

    def t_open_file(self, file):
        data = xlrd.open_workbook(file)
        table = data.sheet_by_index(0)
        for rowNum in range(table.nrows):
            rowVale = table.row_values(rowNum)
            print(rowVale)
            self.widget.signal_cookies_opened.emit(table.nrows, rowNum, 2, rowVale[1])
            self.widget.signal_cookies_opened.emit(table.nrows, rowNum, 0, str(int(rowVale[0])))

    def show_ui_cookies(self, total, row, colum, data):
        self.tableWidget.setRowCount(total)
        item = QTableWidgetItem(data)
        self.tableWidget.setItem(row, colum, item)

    def save_config(self):
        conf_string = json.dumps(dict(self._get_config()))
        with open('./conf', mode='w') as f:
            f.write(conf_string)
        QMessageBox.about(self, '提示', '保存成功')

    def load_config(self):
        with open('./conf', mode='r') as f:
            s = f.read()
            if s:
                conf = Dict(json.loads(s))
                print(conf)
                self.spinBox.setValue(int(conf.thread_num))
                self.lineEdit.setText(conf.sku)
                self.spinBox_2.setValue(int(conf.sku_num))
                self.radioButton_3.setChecked(conf.rush_buy)
                self.radioButton_5.setChecked(conf.fixed_buy)
                self.dateTimeEdit.setDateTime(QDateTime.fromString(conf.buy_time, 'yyyy-MM-dd hh:mm:ss'))

    def _get_config(self):
        # 获取页面的配置项
        conf = Dict()
        conf.thread_num = self.spinBox.text()
        conf.sku = self.lineEdit.text()
        conf.sku_num = self.spinBox_2.text()
        conf.rush_buy = self.radioButton_3.isChecked()
        conf.fixed_buy = self.radioButton_5.isChecked()
        conf.buy_time = self.dateTimeEdit.dateTime().toString('yyyy-MM-dd hh:mm:ss')
        return conf

    def get_cookies(self):
        cookies_list = []
        # column_count = self.tableWidget.columnCount()  # 总列
        row_count = self.tableWidget.rowCount()  # 总行
        for i in range(row_count):
            cookies = self.tableWidget.item(i, 2).text()
            cookies_list.append(cookies)
        return cookies_list

    def update_widget(self, cookies, data, column):
        # column 指定更新哪列
        print(cookies, data, column)
        s = self.tableWidget.findItems(cookies, QtCore.Qt.MatchExactly)
        for i in s:
            item = QTableWidgetItem(data)
            self.tableWidget.setItem(i.row(), column, item)

    def start(self):
        # self.conf = self._get_config()
        # cookies_list = self.get_cookies()
        # self.update_widget('17303419993', '111', 3)
        cookies_list = self.get_cookies()
        conf = self._get_config()
        for cookies in cookies_list:
            thread = Thread(target=self.skill, args=(cookies, conf, self.widget))
            self.queue.put(thread)
            thread.start()


    def skill(self, cookies, conf, widget):
        jd_seckill = JdSeckill(conf.sku, conf.sku_num, conf.buy_time, cookies, widget)
        jd_seckill.seckill_by_proc_pool(work_count=conf.thread_num)

    def test_login(self):
        thread = Thread(target=self.t_test_login)
        thread.start()


    def t_test_login(self):
        cookies_list = self.get_cookies()
        conf = self._get_config()
        for cookies in cookies_list:
            jd_seckill = JdSeckill(conf.sku, conf.sku_num, conf.buy_time, cookies, self.widget)
            jd_seckill.get_username()

    def stop(self):
        while True:
            try:
                thread = self.queue.get(timeout=0.5)
                if thread.isAlive():
                    stop_thread(thread)

            except Exception as e:
                logger.error(e)
                break



class Skill:
    def __init__(self, parent=None):
        super(Skill, self).__init__(parent)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWindow()
    myWin.show()
    sys.exit(app.exec_())
