import hashlib
import random
import re
import http.client
import time
import os
import datetime
import requests
import re
from utils.util import parse_json, Dict


def register(secret):
    md5 = hashlib.md5('6a9a5ba51e2d014bd678f866ee467fd6'.encode(encoding='UTF-8'))
    md5.update(secret.encode(encoding='UTF-8'))
    local_secret = md5.hexdigest()
    print(local_secret)


def get_webserver_time(host):
    conn = http.client.HTTPConnection(host)
    conn.request("GET", "/")
    r = conn.getresponse()
    # r.getheaders() #获取所有的http头
    ts = r.getheader('date')  # 获取http头date部分
    print('ts', ts)

    # 将GMT时间转换成北京时间
    ltime = time.strptime(ts[5:25], "%d %b %Y %H:%M:%S")
    print('ltime', ltime)
    ttime = time.localtime(time.mktime(ltime) + 8 * 60 * 60)
    print('ttime', ttime)
    dat = "%u-%02u-%02u" % (ttime.tm_year, ttime.tm_mon, ttime.tm_mday)
    tm = "%02u:%02u:%02u" % (ttime.tm_hour, ttime.tm_min, ttime.tm_sec)
    print(dat, tm)
    # os.system(dat)
    # os.system(tm)







if __name__ == '__main__':
    pass
    register('f72e4eea3ffae43fb5a1c044cb8f7b52')
    # get_webserver_time('www.jd.com')
    # nowTime = lambda:int(round(time.time() * 1000))
    # print(nowTime())
    # print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
