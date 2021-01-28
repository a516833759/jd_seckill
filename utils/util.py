import json
import random
import requests
import zmail
from jd_logger import logger
import threading
import platform
import hashlib
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

system = platform.system()
if system != 'Darwin':
    import wmi

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
    "Mozilla/5.0 (X11; OpenBSD i386) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.3319.102 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.2309.372 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.2117.157 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1866.237 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/4E423F",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.16 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1623.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36",
    "Mozilla/5.0 (X11; CrOS i686 4319.74.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.2 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1467.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1500.55 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.90 Safari/537.36",
    "Mozilla/5.0 (X11; NetBSD) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36",
    "Mozilla/5.0 (X11; CrOS i686 3912.101.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.14 (KHTML, like Gecko) Chrome/24.0.1292.0 Safari/537.14"
]


class Job(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()  # 用于暂停线程的标识
        self.__flag.set()  # 设置为True
        self.__running = threading.Event()  # 用于停止线程的标识
        self.__running.set()  # 将running设置为True

    # def run(self):
    #     while self.__running.isSet():
    #         self.__flag.wait()   # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回

    def pause(self):
        self.__flag.clear()  # 设置为False, 让线程阻塞

    def resume(self):
        self.__flag.set()  # 设置为True, 让线程停止阻塞

    def stop(self):
        self.__flag.set()  # 将线程从暂停状态恢复, 如何已经暂停的话
        self.__running.clear()  # 设置为False


class Dict(dict):

    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


def parse_json(s):
    try:
        begin = s.find('{')
        end = s.rfind('}') + 1
        return json.loads(s[begin:end])
    except Exception as e:
        logger.error(e)
        return


def get_random_useragent():
    """生成随机的UserAgent
    :return: UserAgent字符串
    """
    return random.choice(USER_AGENTS)


def get_cookies(cookies):
    """解析cookies内容并添加到cookiesJar"""

    manual_cookies = {}
    cookie_string = cookies.strip(';')
    for item in cookie_string.split(';'):
        print(item)
        name, value = item.strip().split('=', 1)
        # 用=号分割，分割1次
        manual_cookies[name] = value
        # 为字典cookies添加内容
    cookiesJar = requests.utils.cookiejar_from_dict(manual_cookies, cookiejar=None, overwrite=True)
    return cookiesJar


def get_session(cookies):
    # 初始化session
    session = requests.session()
    session.headers = {"User-Agent": USER_AGENTS[0],
                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                       "Connection": "keep-alive"}
    checksession = requests.session()
    checksession.headers = {"User-Agent": USER_AGENTS[0],
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                            "Connection": "keep-alive"}
    # 获取cookies保存到session
    session.cookies = get_cookies(cookies)
    return session


def send_email(message):
    """推送信息到微信"""
    server = zmail.server('516833759@qq.com', 'pqebqgebkfbnbija')
    server.send_mail('516833759@qq.com', {'subject': '京东抢购软件通知', 'content_text': message})


class Register:
    def __init__(self):
        self.key = self.get_device_info()

    def get_device_info(self):
        c = wmi.WMI()
        serial_number = c.Win32_DiskDrive()[0].SerialNumber if c.Win32_DiskDrive() else None
        if not serial_number:
            return
        key = hashlib.md5(serial_number.encode(encoding='UTF-8')).hexdigest()
        return key

    def register(self, key, secret):
        md5 = hashlib.md5('6a9a5ba51e2d014bd678f866ee467fd6'.encode(encoding='UTF-8'))
        md5.update(self.key.encode(encoding='UTF-8'))
        local_secret = md5.hexdigest()
        if secret == local_secret:
            with open('./%s' % key, mode='w') as f:
                f.write(secret)
            return True
        return False


def get_cookies_by_browser(widget,headless=False):
    option = webdriver.ChromeOptions()
    option.add_argument('disable-infobars')
    if headless:
        option.add_argument('headless')
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    browser = webdriver.Chrome(executable_path='./chromedriver', chrome_options=option)
    browser.get('https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F%3Fcountry%3DUSA')
    if headless and widget:
        scan_img_xpath = '//*[@id="content"]/div[2]/div[1]/div/div[5]/div/div[2]/div[1]/img'
        scan_img = browser.find_element_by_xpath(scan_img_xpath).get_attribute('src')
        widget.signal_login_scan_code.emit('%s'%scan_img)
    try:
        locator = (By.XPATH, '//*[@id="shortcut"]/div/ul[2]/li[3]/div/a')
        name_locator = (By.XPATH,'//*[@id="ttbar-login"]/div[1]/a')
        WebDriverWait(browser, 20, 0.5).until(EC.presence_of_element_located(locator))
        href = browser.find_element_by_xpath('//*[@id="shortcut"]/div/ul[2]/li[3]/div/a').get_attribute('href')
        name = browser.find_element_by_xpath('//*[@id="ttbar-login"]/div[1]/a').text
        print(name)
        print(href)
        browser.get(href)
        cookies_list = browser.get_cookies()
        cookies_str = ''
        for cookies in cookies_list:
            s = '%s=%s;' % (cookies.get('name'), cookies.get('value'))
            cookies_str += s
        print('cookies_str',cookies_str)
        widget.signal_login_cookies.emit(cookies_str,name)
    except Exception as e:
        print(e)
    finally:
        browser.close()


if __name__ == '__main__':
    # register = Register()
    # register.register('111')
    # print(platform.system())
    get_cookies_by_browser()
