import sys
import os
import xlrd

from PyQt5.QtCore import pyqtSignal, QDateTime
from PyQt5.QtWidgets import *
from jd_main_ui import *
from register import *
import threading
from jd_logger import logger
from utils.util import Dict
from jd_spider_requests import JdSeckill
import json
import queue
import platform
from utils.util import Register






class MyWidget(QWidget):
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
        self.tableWidget.setColumnCount(9)
        self.tableWidget.setHorizontalHeaderLabels(['id', '用户', 'cookies', '登录状态', '订单号', '商品', '下单状态', '日志','错误码'])
        self.tableWidget.setColumnWidth(7,300)
        self.toolButton.clicked.connect(self.open_file)
        self.pushButton_4.clicked.connect(self.start)
        self.pushButton_6.clicked.connect(self.save_config)
        self.pushButton_7.clicked.connect(self.test_login)
        self.pushButton_5.clicked.connect(self.stop)
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        self.load_config()
        self.queue = queue.Queue(maxsize=100)
        self.action.triggered.connect(self.show_register)
        self.system = platform.system()
        if self.system != 'Darwin':
            self.device = Register()
            self.register(init=True)

    def show_register(self):
        key = self.device.get_device_info()
        self.di = QDialog()
        self.d = Ui_Dialog()
        self.d.setupUi(self.di)
        self.di.show()
        self.d.lineEdit.setText(key)
        self.d.buttonBox.clicked.connect(self.register)

    def register(self,init=False):
        if self.system == 'Darwin':
            self.enabled()
            return
        if init == True:
            if not os.path.exists('./%s' % self.device.get_device_info()):
                self.disabled()
                return
            else:
                key = self.device.get_device_info()
                with open('./%s' % key,mode='r') as f:
                    secret = f.read()
                status = self.device.register(key, secret)
                if not status:
                    self.disabled()
                else:
                    self.enabled()
        else:
            key = self.d.lineEdit.text()
            secret = self.d.lineEdit_2.text()
            status = self.device.register(key,secret)
            if not status:
                self.disabled()
            else:
                self.enabled()
                QMessageBox.about(self, '提示', '激活成功')
    def disabled(self):
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        self.pushButton_4.setEnabled(False)
        self.pushButton_5.setEnabled(False)
        self.pushButton_6.setEnabled(False)
        self.pushButton_7.setEnabled(False)
    def enabled(self):
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.pushButton_3.setEnabled(True)
        self.pushButton_4.setEnabled(True)
        self.pushButton_5.setEnabled(True)
        self.pushButton_6.setEnabled(True)
        self.pushButton_7.setEnabled(True)
    def open_file(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                   "xls Files(*.xls)")
        if not fileName:
            return
        thread = threading.Thread(target=self.t_open_file, args=(fileName,))
        thread.start()

    def t_open_file(self, file):
        data = xlrd.open_workbook(file)
        table = data.sheet_by_index(0)
        for rowNum in range(table.nrows):
            rowVale = table.row_values(rowNum)
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
        if not os.path.exists('./conf'):
            return
        with open('./conf', mode='r') as f:
            s = f.read()
            if s:
                conf = Dict(json.loads(s))
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
        s = self.tableWidget.findItems(cookies, QtCore.Qt.MatchExactly)
        for i in s:
            item = QTableWidgetItem(data)
            self.tableWidget.setItem(i.row(), column, item)

    def start(self):
        cookies_list = self.get_cookies()
        if len(cookies_list) == 0:
            QMessageBox.about(self, '提示', '请导入cookies数据')
            return
        self.pushButton_4.setEnabled(False)
        self.pushButton_5.setEnabled(True)
        conf = self._get_config()
        for cookies in cookies_list:
            # thread = threading.Thread(target=self.skill, args=(cookies, conf, self.widget))
            thread = JdSeckill(conf.sku, conf.sku_num, conf.buy_time, cookies, self.widget)
            self.queue.put(thread)
            thread.start()

            # jd_seckill.seckill_by_proc_pool(work_count=conf.thread_num)
            # thread.start()

    def skill(self, cookies, conf, widget):
        jd_seckill = JdSeckill(conf.sku, conf.sku_num, conf.buy_time, cookies, widget)
        jd_seckill.seckill_by_proc_pool(work_count=conf.thread_num)

    def test_login(self):
        thread = threading.Thread(target=self.t_test_login)
        thread.start()


    def t_test_login(self):
        cookies_list = self.get_cookies()
        conf = self._get_config()
        for cookies in cookies_list:
            jd_seckill = JdSeckill(conf.sku, conf.sku_num, conf.buy_time, cookies, self.widget)
            jd_seckill.get_username()

    def stop(self):
        self.pushButton_4.setEnabled(True)
        self.pushButton_5.setEnabled(False)
        while True:
            try:
                thread = self.queue.get(timeout=0.1)
                if thread.isAlive():
                    thread.stop()
            except Exception as e:
                logger.error(e)
                break


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWindow()
    myWin.show()
    sys.exit(app.exec_())
