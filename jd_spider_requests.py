import json
import random
import sys
import time
from jd_logger import logger
from timer import Timer
import requests
from utils.util import parse_json, get_session, send_email, USER_AGENTS, Dict
# from concurrent.futures import ProcessPoolExecutor
from lxml import etree
import threadpool
import threading


class JdSeckill(threading.Thread):
    def __init__(self, sku, sku_num, buy_time, cookies, widget, *args, **kwargs):
        # 初始化信息
        super(JdSeckill, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()  # 用于暂停线程的标识
        self.__flag.set()  # 设置为True
        self.__running = threading.Event()  # 用于停止线程的标识
        self.__running.set()  # 将running设置为True

        self.session = get_session(cookies)
        self.sku_id = sku
        self.seckill_num = sku_num
        self.seckill_init_info = dict()
        self.seckill_url = dict()
        self.seckill_order_data = dict()
        self.default_user_agent = USER_AGENTS[0]
        self.buy_time = buy_time
        self.widget = widget
        self.cookies = cookies

    def get_yuyue_info(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
            'cookie': 'shshshfpa=85bcc8b7-a2cf-6331-6d20-1e9b7570bd07-1582600259; shshshfpb=85bcc8b7-a2cf-6331-6d20-1e9b7570bd07-1582600259; ipLocation=%u5317%u4eac; _base_=YKH2KDFHMOZBLCUV7NSRBWQUJPBI7JIMU5R3EFJ5UDHJ5LCU7R2NILKK5UJ6GLA2RGYT464UKXAI4Z6HPCTN4UQM3WHVQ4ENFP57OCZ5N2N2URBURR6MWC2MNWI5TCDLSCF555UOYV4EBYV2VFBXBYOERNZELA6E4S4L2GLWBLTAIW5N6ZGEONMNNA5DQRDPVL52KNRE2QP7OBV5ICKFL7IQOAG4MEKLVTSGRNGZJL5VKB43KA2SZT3SGK7LGDLE5SE3OZKBF32H4DADFQ2AL2NBKMPYN3AUVRGT3FGPXTDJ7MB2MUSZQMNOQ35UDUZ7IDFC7UCAGXMFSRTPEMNBD2OZDSSGZYQR5Q4YWI3JTXJWJPEGFXPFMTCFS2DG5VRCSYCGVYLKJLDUG; user-key=562cbefe-322e-419b-adf5-f93571000a23; pinId=QN1q7VZjGgbBJqKyyYWCow; pin=3248884568; unick=%E4%B8%9C%E4%BA%AC%E4%BC%9A%E5%91%98VIP; _tp=Cm4nrHC1g4CVdkf5st5g%2FQ%3D%3D; _pst=3248884568; __jdu=16119939521361622463629; areaId=1; __jdv=76161171%7Ciosapp%7Ct_335139774%7Cappshare%7CQqfriends%7C1612012344027; ceshi3.com=201; TrackID=1J-tNfRRfCG7I_y7bBcT7FUv1eQFSBV3Br6zsGgK9K-dBGivXIlpTCu2xUqVk6VtEe8vi2iDV_5qwEjeinJRssN_3gEEQEd8XJ2J64TN0d4xJxjhNn5Q-x0PzjvyPRtfQ; cn=14; ipLoc-djd=6-303-36780-56048.138527709; mt_xid=V2_52007VwMVUl1QWlgXTRpcB2ADFVFeXVVYGEoRbFEwA0YBXFsHRk1IGAgZYgcSWkELW1MYVU1fVTJXQVRVX1BSS3kaXQZnHxNRQVlSSx9JEl8FbAAaYl9oUmoXSRpfAGAEFFtVXVtYHk4YXQNhMxdTVF4%3D; __jda=122270672.16119939521361622463629.1611993952.1612155258.1612157208.9; __jdc=122270672; 3AB9D23F7A4B3C9B=CWWLN6K2UUYVALSZPHMSG6WQVSSTHJOATAOZK4CDGPADXGCNHG5MNBJZTOIJHAZJN42V7ORYOHAD6MCQCNCFDQSIVM; shshshfp=709a8342f21c895478343eab27de6449; shshshsID=39f53fe326c5f4cae35f0b23a1c5d80f_8_1612159356102; __jdb=122270672.9.16119939521361622463629|9.1612157208; thor=77F3250B9693C119CC90EB6BB73E1B2E4359907CA7AA269ACA99D31B927C158FD0E816CD55200594AA37DC94C73DD2C35FCAE06F4EC57B08F5E7BD8672771275A154B528F886C14D17BA326C8FEEFAE09A1B5135A9DF00FD6E63351F32CA0319F07016B9841C914C76AD4D9A638172F823F93E31F9B7E902C475E3D6DCBB7E17040615219B011520CDC2ABEF16A70BBC'
        }
        params = {
            'callback': 'jQuery%s' % random.randint(1000000, 9999999),
            'skuId': self.sku_id,
            'cat': '12259,12260,9435',
            'area': '6_303_36780_56048',
            'shopId': '1000085463',
            'venderId': '1000085463',
            'paramJson': {"platform2": "1", "specialAttrStr": "p0pp1pppppppppppppppppp", "skuMarkStr": "00"}
        }
        resp = parse_json(self.session.get('https://item-soa.jd.com/getWareBusiness', headers=headers, params=params).text)
        print('商品预约数据',resp)
        info = Dict({
            'buy_time': resp.yuyueInfo.get('buyTime')[:16],  # 2021-02-02 12:00-2021-02-02 12:30
            'countdown': resp.yuyueInfo.get('countdown'),  # 倒计时s
            'yuyueTime': resp.yuyueInfo.get('yuyueTime')[:16],  # "2021-02-02 10:00~2021-02-02 11:59"
            'yuyue': resp.yuyueInfo.get('yuyue')  # 是否预约 True
        })
        self.widget.signal_yuyue_info.emit(json.dumps(info))
        if info.yuyue:
            self.widget.signal_login.emit(self.cookies, '已经预约', 0)
        else:
            self.widget.signal_login.emit(self.cookies, '未预约', 0)


    def pause(self):
        self.__flag.clear()  # 设置为False, 让线程阻塞

    def resume(self):
        self.__flag.set()  # 设置为True, 让线程停止阻塞

    def stop(self):
        self.__flag.set()  # 将线程从暂停状态恢复, 如何已经暂停的话
        self.__running.clear()  # 设置为False

    def reserve(self):
        """
        预约
        """
        self.__reserve()

    def seckill(self, i):
        """
        抢购
        """
        self.__seckill()

    def wati_some_time(self):
        time.sleep(random.randint(5000, 8000) / 10000)

    def get_sku_title(self):
        """获取商品名称"""
        url = 'https://item.jd.com/{}.html'.format(self.sku_id)
        resp = self.session.get(url).content
        x_data = etree.HTML(resp)
        sku_title = x_data.xpath('/html/head/title/text()')
        return sku_title[0]

    def run(self, work_count=5):
        """
        多进程进行抢购
        work_count：进程数量
        """
        # with ProcessPoolExecutor(work_count) as pool:
        #     for i in range(work_count):
        #         pool.submit(self.seckill)
        pool = threadpool.ThreadPool(int(work_count))
        reqs = threadpool.makeRequests(self.seckill, [i for i in range(int(work_count))])
        [pool.putRequest(req) for req in reqs]  # 多线程一块执行
        pool.wait()

    def __reserve(self):
        """
        预约
        """
        self.login()
        try:
            self.make_reserve()
        except Exception as e:
            logger.info('预约发生异常!', e)

    def __seckill(self):
        """
        抢购
        """
        self.login()
        while self.__running.isSet():
            self.__flag.wait()
            try:
                self.request_seckill_url()
                self.request_seckill_checkout_page()
                self.submit_seckill_order()
            except Exception as e:
                logger.error('抢购发生异常，稍后继续执行！', e)
            self.wati_some_time()

    def login(self):
        for flag in range(1, 3):
            try:
                targetURL = 'https://order.jd.com/center/list.action'
                payload = {
                    'rid': str(int(time.time() * 1000)),
                }
                resp = self.session.get(
                    url=targetURL, params=payload, allow_redirects=False)
                if resp.status_code == requests.codes.OK:
                    logger.info('校验是否登录[成功]')
                    self.push_log('校验是否登录[成功]')
                    logger.info('用户:{}'.format(self.get_username()))
                    return True
                else:
                    logger.info('校验是否登录[失败]')
                    self.push_log('校验是否登录[失败]')

                    logger.info('请重新输入cookie')
                    time.sleep(1)
                    continue
            except Exception as e:
                logger.info('第【%s】次失败请重新获取cookie', flag)
                time.sleep(1)
                continue
        sys.exit(1)

    def make_reserve(self):
        """商品预约"""
        logger.info('商品名称:{}'.format(self.get_sku_title()))
        url = 'https://yushou.jd.com/youshouinfo.action?'
        payload = {
            'callback': 'fetchJSON',
            'sku': self.sku_id,
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.default_user_agent,
            'Referer': 'https://item.jd.com/{}.html'.format(self.sku_id),
        }
        resp = self.session.get(url=url, params=payload, headers=headers)
        if not resp.text:
            logger.error('未获取返回数据')
            return
        resp_json = parse_json(resp.text)
        reserve_url = resp_json.get('url')
        self.timers = Timer(self.buy_time)
        self.timers.start()
        while self.__running.isSet():
            self.__flag.wait()
            try:
                self.session.get(url='https:' + reserve_url)
                logger.info('预约成功，已获得抢购资格 / 您已成功预约过了，无需重复预约')
                success_message = "预约成功，已获得抢购资格 / 您已成功预约过了，无需重复预约"
                send_email(success_message)
                break
            except Exception as e:
                logger.error('预约失败,错误：', e)
                time.sleep(3)

    def get_username(self):
        """获取用户信息"""
        url = 'https://passport.jd.com/user/petName/getUserInfoForMiniJd.action'
        payload = {
            'callback': 'jQuery'.format(random.randint(1000000, 9999999)),
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.default_user_agent,
            'Referer': 'https://order.jd.com/center/list.action',
        }

        resp = self.session.get(url=url, params=payload, headers=headers)

        try_count = 5
        while not resp.text.startswith("jQuery"):
            try_count = try_count - 1
            if try_count > 0:
                resp = self.session.get(url=url, params=payload, headers=headers)
            else:
                break
            self.wati_some_time()
        # 响应中包含了许多用户信息，现在在其中返回昵称
        # jQuery2381773({"imgUrl":"//storage.360buyimg.com/i.imageUpload/xxx.jpg","lastLoginTime":"","nickName":"xxx","plusStatus":"0","realName":"xxx","userLevel":x,"userScoreVO":{"accountScore":xx,"activityScore":xx,"consumptionScore":xxxxx,"default":false,"financeScore":xxx,"pin":"xxx","riskScore":x,"totalScore":xxxxx}})
        if not resp.text:
            logger.error('未获取返回数据')
            self.push_log('未获取返回数据')
            return

        logger.info('测试登录返回resp.text', parse_json(resp.text))
        nick_name = parse_json(resp.text).get('nickName')
        if not nick_name:
            self.widget.signal_login.emit(self.cookies, '登录失败', 3)
        else:
            self.push_log('登录成功')
            self.widget.signal_login.emit(self.cookies, nick_name, 1)
            self.widget.signal_login.emit(self.cookies, '登录成功', 3)
            return nick_name

    def get_seckill_url(self):
        """获取商品的抢购链接
        点击"抢购"按钮后，会有两次302跳转，最后到达订单结算页面
        这里返回第一次跳转后的页面url，作为商品的抢购链接
        :return: 商品的抢购链接
        """
        url = 'https://itemko.jd.com/itemShowBtn'
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'skuId': self.sku_id,
            'from': 'pc',
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.default_user_agent,
            'Host': 'itemko.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(self.sku_id),
        }
        while self.__running.isSet():
            self.__flag.wait()
            resp = self.session.get(url=url, headers=headers, params=payload)
            print('resp', resp.text)
            if not resp.text:
                logger.error('未获取返回数据')
                return
            resp_json = parse_json(resp.text)
            if resp_json.get('url'):
                # https://divide.jd.com/user_routing?skuId=8654289&sn=c3f4ececd8461f0e4d7267e96a91e0e0&from=pc
                router_url = 'https:' + resp_json.get('url')
                # https://marathon.jd.com/captcha.html?skuId=8654289&sn=c3f4ececd8461f0e4d7267e96a91e0e0&from=pc
                seckill_url = router_url.replace(
                    'divide', 'marathon').replace(
                    'user_routing', 'captcha.html')
                if seckill_url:
                    msg = "抢购链接获取成功: %s", seckill_url
                    logger.info(msg)
                    self.push_log(msg)
                    return seckill_url
                else:
                    msg = "抢购链接获取失败"
                    return
            else:
                logger.info("抢购链接获取失败，稍后自动重试")
                self.push_log("抢购链接获取失败，稍后自动重试")
                self.wati_some_time()

    def push_log(self, msg):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        msg = '%s--%s' % (current_time, msg)
        self.widget.signal_add_log.emit(self.cookies, msg, 7)

    def push_err_code(self, msg):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        msg = '%s--%s' % (current_time, msg)
        self.widget.signal_add_log.emit(self.cookies, msg, 8)

    def push_order_code(self, msg):
        self.widget.signal_add_log.emit(self.cookies, msg, 4)

    def request_seckill_url(self):
        """访问商品的抢购链接（用于设置cookie等"""
        user_name = '用户:{}'.format(self.get_username())
        title = '商品名称:{}'.format(self.get_sku_title())
        logger.info(title)

        logger.info(user_name)
        self.push_log(user_name)
        # self.timers = Timer(self.buy_time)

        self.push_log('正在等待到达设定时间:%s' % self.buy_time)
        self.timers.start()
        self.seckill_url[self.sku_id] = self.get_seckill_url()
        logger.info('访问商品的抢购连接...')
        self.push_log('访问商品的抢购连接...')
        headers = {
            'User-Agent': self.default_user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(self.sku_id),
        }
        if not self.seckill_url.get(self.sku_id):
            self.push_log('未获取商品的抢购连接...')
            return
        self.session.get(
            url=self.seckill_url.get(
                self.sku_id),
            headers=headers,
            allow_redirects=False)

    def request_seckill_checkout_page(self):
        """访问抢购订单结算页面"""
        logger.info('访问抢购订单结算页面...')
        self.push_log('访问抢购订单结算页面...')
        url = 'https://marathon.jd.com/seckill/seckill.action'
        payload = {
            'skuId': self.sku_id,
            'num': self.seckill_num,
            'rid': int(time.time())
        }
        headers = {
            'User-Agent': self.default_user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(self.sku_id),
        }
        self.session.get(url=url, params=payload, headers=headers, allow_redirects=False)

    def _get_seckill_init_info(self):
        """获取秒杀初始化信息（包括：地址，发票，token）
        :return: 初始化信息组成的dict
        """
        logger.info('获取秒杀初始化信息...')
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/init.action'
        data = {
            'sku': self.sku_id,
            'num': self.seckill_num,
            'isModifyAddress': 'false',
        }
        headers = {
            'User-Agent': self.default_user_agent,
            'Host': 'marathon.jd.com',
        }
        resp = self.session.post(url=url, data=data, headers=headers)
        if not resp.text:
            logger.error('秒杀初始化信息未获取返回数据')
            self.push_log('秒杀初始化信息未获取返回数据')
            return
        return parse_json(resp.text)

    def _get_seckill_order_data(self):
        """生成提交抢购订单所需的请求体参数
        :return: 请求体参数组成的dict
        """
        logger.info('生成提交抢购订单所需参数...')
        self.push_log('生成提交抢购订单所需参数...')
        # 获取用户秒杀初始化信息
        self.seckill_init_info[self.sku_id] = self._get_seckill_init_info()
        init_info = self.seckill_init_info.get(self.sku_id)
        if not init_info:
            return
        default_address = init_info['addressList'][0]  # 默认地址dict
        invoice_info = init_info.get('invoiceInfo', {})  # 默认发票信息dict, 有可能不返回
        token = init_info['token']
        data = {
            'skuId': self.sku_id,
            'num': self.seckill_num,
            'addressId': default_address['id'],
            'yuShou': 'true',
            'isModifyAddress': 'false',
            'name': default_address['name'],
            'provinceId': default_address['provinceId'],
            'cityId': default_address['cityId'],
            'countyId': default_address['countyId'],
            'townId': default_address['townId'],
            'addressDetail': default_address['addressDetail'],
            'mobile': default_address['mobile'],
            'mobileKey': default_address['mobileKey'],
            'email': default_address.get('email', ''),
            'postCode': '',
            'invoiceTitle': invoice_info.get('invoiceTitle', -1),
            'invoiceCompanyName': '',
            'invoiceContent': invoice_info.get('invoiceContentType', 1),
            'invoiceTaxpayerNO': '',
            'invoiceEmail': '',
            'invoicePhone': invoice_info.get('invoicePhone', ''),
            'invoicePhoneKey': invoice_info.get('invoicePhoneKey', ''),
            'invoice': 'true' if invoice_info else 'false',
            'password': '',
            'codTimeType': 3,
            'paymentType': 4,
            'areaCode': '',
            'overseas': 0,
            'phone': '',
            'eid': 'A3O455IQ4JLN4EUPIZTI4DZKMSDWCPY4VNJHXVAOU4NLKWSGNO6NDN53TO7RRPVDJVTELS4ZPMWANTKAULVGL7A3B4',
            'fp': 'ffa84dac986b8570d2d4ec69dcda19db',
            'token': token,
            'pru': ''
        }
        return data

    def submit_seckill_order(self):
        """提交抢购（秒杀）订单
        :return: 抢购结果 True/False
        """
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/submitOrder.action'
        payload = {
            'skuId': self.sku_id,
        }
        self.seckill_order_data[self.sku_id] = self._get_seckill_order_data()
        logger.info('提交抢购订单...')
        self.push_log('提交抢购订单...')
        headers = {
            'User-Agent': self.default_user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://marathon.jd.com/seckill/seckill.action?skuId={0}&num={1}&rid={2}'.format(
                self.sku_id, self.seckill_num, int(time.time())),
        }
        resp = self.session.post(
            url=url,
            params=payload,
            data=self.seckill_order_data.get(
                self.sku_id),
            headers=headers)
        if not resp.text:
            logger.error('未获取返回数据')
            return
        resp_json = parse_json(resp.text)
        # 返回信息
        # 抢购失败：
        # {'errorMessage': '很遗憾没有抢到，再接再厉哦。', 'orderId': 0, 'resultCode': 60074, 'skuId': 0, 'success': False}
        # {'errorMessage': '抱歉，您提交过快，请稍后再提交订单！', 'orderId': 0, 'resultCode': 60017, 'skuId': 0, 'success': False}
        # {'errorMessage': '系统正在开小差，请重试~~', 'orderId': 0, 'resultCode': 90013, 'skuId': 0, 'success': False}
        # 抢购成功：
        # {"appUrl":"xxxxx","orderId":820227xxxxx,"pcUrl":"xxxxx","resultCode":0,"skuId":0,"success":true,"totalMoney":"xxxxx"}
        if resp_json and resp_json.get('success'):
            order_id = resp_json.get('orderId')
            total_money = resp_json.get('totalMoney')
            pay_url = 'https:' + resp_json.get('pcUrl')
            logger.info(
                '抢购成功，订单号:{}, 总价:{}, 电脑端付款链接:{}'.format(order_id, total_money, pay_url)
            )
            success_message = "抢购成功，订单号:{}, 总价:{}, 电脑端付款链接:{}".format(order_id, total_money, pay_url)
            self.push_order_code(str(order_id))
            send_email(success_message)
            return True
        else:
            err_msg = '抢购失败，返回信息:{}'.format(str(resp_json))
            logger.error(err_msg)
            self.push_log(err_msg)
            error_message = '抢购失败，返回信息:{}'.format(resp_json)
            if resp_json and resp_json.get('resultCode'):
                self.push_err_code(resp_json.get('resultCode'))
            return False
