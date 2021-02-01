import re
import sys
import os
import time

import xlrd
from PyQt5.QtCore import pyqtSignal, QDateTime, QUrl
# from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QMainWindow, QDialog, QTableWidgetItem, QMessageBox, QFileDialog, QApplication, \
    QButtonGroup

from jd_main_ui import *
from register import *
from sacn_login import Ui_Dialog as Login_Dialog
import threading
from jd_logger import logger
from utils.util import Dict
from jd_spider_requests import JdSeckill
import json
import queue
import platform
from utils.util import Register, get_cookies_by_browser
import requests


class MyWidget(QWidget):
    signal_add_log = pyqtSignal(str, str, int)
    signal_cookies_opened = pyqtSignal(int, int, int, str)
    signal_login = pyqtSignal(str, str, int)
    signal_login_scan_code = pyqtSignal(str)
    signal_login_cookies = pyqtSignal(str, str)
    signal_yuyue_info = pyqtSignal(str)


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        self.widget = MyWidget()
        self.widget.signal_cookies_opened.connect(self.show_ui_cookies)
        self.widget.signal_login.connect(self.update_widget)
        self.widget.signal_login_scan_code.connect(self.show_scan_code)
        self.widget.signal_login_cookies.connect(self.show_cookies)
        self.widget.signal_add_log.connect(self.update_widget)
        self.widget.signal_yuyue_info.connect(self.show_info)
        self.tableWidget.setColumnCount(9)
        self.tableWidget.setHorizontalHeaderLabels(['是否预约', '用户', 'cookies', '登录状态', '订单号', '商品', '下单状态', '日志', '错误码'])
        self.tableWidget.setColumnWidth(7, 300)
        self.toolButton.clicked.connect(self.open_file)
        self.pushButton_4.clicked.connect(self.start)
        self.pushButton_6.clicked.connect(self.save_config)
        self.pushButton_7.clicked.connect(self.test_login)
        self.pushButton_5.clicked.connect(self.stop)
        self.pushButton_2.setEnabled(False)
        self.radioButton_4.setEnabled(False)
        self.radioButton_6.setChecked(True)
        self.pushButton_3.clicked.connect(self.download)
        self.pushButton_8.clicked.connect(self.start_count)
        self.pushButton.clicked.connect(self.login)
        self.lineEdit.setText('https://item.jd.com/100009838041.html')
        self.load_config()
        self.queue = queue.Queue(maxsize=100)
        self.queue_stop = queue.Queue(maxsize=100)
        self.action.triggered.connect(self.show_register)
        self.system = platform.system()
        self.time = QTimer(self)
        self.time.setInterval(1000)
        self.time.timeout.connect(self.refresh_count)
        self.count = 0
        self.yuyue_info = {}
        self.load_cookies()

        if self.system != 'Darwin':
            self.device = Register()
            self.register(init=True)

    def show_info(self, info):
        info = Dict(json.loads(info))
        print('info', info)
        self.yuyue_info = info
        if not self.time.isActive():
            self.count = info.countdown
            self.start_count()
        else:
            self.add_log('倒计时已经开始')

        current_buy_time = self.dateTimeEdit.dateTime().toString('yyyy-MM-dd hh:mm:ss')
        if '%s:00' % info.buy_time == current_buy_time:
            self.add_log('自动核对抢购时间无误')
        else:
            status = QMessageBox.information(None, '消息提示', '当前设置时间与抢购时间不一致，知否自动更新', QMessageBox.Yes | QMessageBox.No)
            if status == QMessageBox.Yes:
                self.dateTimeEdit.setDateTime(QDateTime.fromString('%s:00' % info.buy_time, 'yyyy-MM-dd hh:mm:ss'))
                self.add_log('自动更新抢购时间成功')

    def start_count(self):
        if not self.yuyue_info:
            self.add_log('获取预约基本信息')
            self.get_yuyue_info()
        if not self.time.isActive():
            self.add_log('倒计时开始')
            self.time.start()
        else:
            self.add_log('倒计时已经开始，请勿重复点击')

    def refresh_count(self):
        if self.count <= 0:
            self.time.stop()
            while True:
                try:
                    thread = self.queue.get(timeout=0.01)
                    self.queue_stop.put(thread)
                    if not thread.isAlive():
                        thread.start()
                except Exception as e:
                    logger.error(e)
                    self.add_log('所有线程启动成功')
                    break
            return
        self.count -= 1
        self.lcdNumber.display(self.count)

    def add_log(self, msg):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        self.textBrowser.append('%s--%s' % (current_time, msg))

    def login(self):
        if self.radioButton_6.isChecked():
            # 电脑网页登录
            t = threading.Thread(target=get_cookies_by_browser, args=(self.widget,))
            t.start()
        else:
            t = threading.Thread(target=get_cookies_by_browser, args=(self.widget, True))
            t.start()
            # get_cookies_by_browser()

    def show_scan_code(self, src):
        print(src)
        self.di = QDialog()
        self.d = Login_Dialog()
        self.d.setupUi(self.di)
        self.d.textBrowser.load(QUrl(str(src)))
        self.di.show()
        self.d.pushButton.clicked.connect(self.add_user)

    def show_cookies(self, cookies, name):
        print(name)
        print(cookies)
        self.add_user(cookies, name)

    def add_user(self, cookies, name=None):
        s = self.tableWidget.findItems(cookies, QtCore.Qt.MatchExactly)
        if len(s) > 0:
            QMessageBox.about(self, '提示', '该用户已存在')
            return
        rowcount = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(rowcount + 1)
        item = QTableWidgetItem(cookies)
        item_name = QTableWidgetItem(name)
        self.tableWidget.setItem(rowcount, 2, item)
        self.tableWidget.setItem(rowcount, 1, item_name)
        self.save_cookies(cookies)
        # QMessageBox.about(self, '提示', '添加成功')

    def save_cookies(self, cookies):
        # 把用户扫码登录成功的cookies数据保存在本地
        with open('./cookies',mode='a+') as f:
            f.seek(0,0)
            cookies_list = f.readlines()
            print('cookies_list',cookies_list)
            if not cookies in [cookies.strip() for cookies in cookies_list]:
                print('cookies',cookies)
                f.seek(0,2)
                f.write('%s\r\n' % cookies)


    def load_cookies(self):
        # 软件开自动加载本地cookies数据
        if not os.path.exists('./cookies'):
            return
        with open('./cookies',mode='r') as f:
            cookies_list = f.readlines()
            # print(cookies_list)
        for cookies in cookies_list:
            if len(cookies.strip())>0:
                self.add_user(cookies.strip())

    def update_widget(self, cookies, data, column):
        # column 指定更新哪列
        s = self.tableWidget.findItems(cookies, QtCore.Qt.MatchExactly)
        for i in s:
            item = QTableWidgetItem(data)
            self.tableWidget.setItem(i.row(), column, item)

    def download(self):
        url = 'https://lijia-dev-public.oss-cn-beijing.aliyuncs.com/0/cookies.xls'
        file_content = requests.get(url).content
        filename = QFileDialog.getSaveFileName(self, '保存文件', 'cookies.xls')
        if not filename[0]:
            return
        with open(filename[0], 'wb+') as f:
            f.write(file_content)
        QMessageBox.about(self, '提示', '下载成功')

    def download_ck(self):
        url = 'https://lijia-dev-public.oss-cn-beijing.aliyuncs.com/0/%E4%BA%AC%E4%B8%9Cck%E6%8F%90%E5%8F%96.zip'
        file_content = requests.get(url).content
        filename = QFileDialog.getSaveFileName(self, '保存文件', '京东ck提取.zip')
        if not filename[0]:
            return
        with open(filename[0], 'wb+') as f:
            f.write(file_content)
        QMessageBox.about(self, '提示', '下载成功')

    def show_register(self):
        key = self.device.get_device_info()
        self.di = QDialog()
        self.d = Ui_Dialog()
        self.d.setupUi(self.di)
        self.di.show()
        self.d.lineEdit.setText(key)
        self.d.buttonBox.clicked.connect(self.register)

    def register(self, init=False):
        if self.system == 'Darwin':
            self.enabled()
            return
        if init == True:
            if not os.path.exists('./%s' % self.device.get_device_info()):
                self.disabled()
                return
            else:
                key = self.device.get_device_info()
                with open('./%s' % key, mode='r') as f:
                    secret = f.read()
                status = self.device.register(key, secret)
                if not status:
                    self.disabled()
                else:
                    self.enabled()
        else:
            key = self.d.lineEdit.text()
            secret = self.d.lineEdit_2.text()
            status = self.device.register(key, secret)
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
                self.radioButton_6.setChecked(conf.login_browser)
                self.radioButton_4.setChecked(not conf.login_browser)

    def _get_config(self):
        # 获取页面的配置项
        conf = Dict()
        conf.thread_num = self.spinBox.text()
        conf.sku = re.search('\\d+', self.lineEdit.text()).group()
        conf.sku_num = self.spinBox_2.text()
        conf.rush_buy = self.radioButton_3.isChecked()
        conf.fixed_buy = self.radioButton_5.isChecked()
        conf.buy_time = self.dateTimeEdit.dateTime().toString('yyyy-MM-dd hh:mm:ss')
        conf.login_browser = True if self.radioButton_6.isChecked() else False
        return conf

    def get_cookies(self):
        cookies_list = []
        # column_count = self.tableWidget.columnCount()  # 总列
        row_count = self.tableWidget.rowCount()  # 总行
        for i in range(row_count):
            cookies = self.tableWidget.item(i, 2).text()
            cookies_list.append(cookies)
        return cookies_list

    def start(self):
        cookies_list = self.get_cookies()
        if len(cookies_list) == 0:
            QMessageBox.about(self, '提示', '请添加账户')
            return
        self.pushButton_4.setEnabled(False)
        self.pushButton_5.setEnabled(True)
        conf = self._get_config()
        self.queue.queue.clear()
        self.test_login()
        for cookies in cookies_list:
            thread = JdSeckill(conf.sku, conf.sku_num, conf.buy_time, cookies, self.widget)
            self.queue.put(thread)
            # thread.start()
        else:
            self.add_log('所有线程已经准备完毕，开始倒计时')

    def skill(self, cookies, conf, widget):
        jd_seckill = JdSeckill(conf.sku, conf.sku_num, conf.buy_time, cookies, widget)
        jd_seckill.seckill_by_proc_pool(work_count=conf.thread_num)

    def test_login(self):
        thread = threading.Thread(target=self.t_test_login)
        thread.start()

    def t_test_login(self):
        cookies_list = self.get_cookies()
        conf = self._get_config()
        self.get_yuyue_info()
        for cookies in cookies_list:
            jd_seckill = JdSeckill(conf.sku, conf.sku_num, conf.buy_time, cookies, self.widget)
            jd_seckill.get_username()

    def get_yuyue_info(self):
        cookies_list = self.get_cookies()
        conf = self._get_config()
        if len(cookies_list) > 0:
            jd_seckill = JdSeckill(conf.sku, conf.sku_num, conf.buy_time, cookies_list[0], self.widget)
            jd_seckill.get_yuyue_info()
        else:
            QMessageBox.about(self, '提示', '请添加账户')

    def stop(self):
        self.pushButton_4.setEnabled(True)
        self.pushButton_5.setEnabled(False)
        while True:
            try:
                thread = self.queue_stop.get(timeout=0.1)
                if thread.isAlive():
                    thread.stop()
            except Exception as e:
                logger.error(e)
                break


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWindow()
    r1 = QButtonGroup(myWin)  # 创建按钮组
    r1.addButton(myWin.radioButton_4)  # 添加按钮
    r1.addButton(myWin.radioButton_6)
    r2 = QButtonGroup()
    r2.addButton(myWin.radioButton)
    r2.addButton(myWin.radioButton_2)
    myWin.setWindowIcon(QIcon('icon/京东-01.png'))
    myWin.show()
    sys.exit(app.exec_())
