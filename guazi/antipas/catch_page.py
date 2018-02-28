# _*_ coding:utf-8 _*_
"""
网页采取了cookies反爬策略
antipas是关键的cookie
"""
import requests
import re
import time
import execjs
import socket
import random
import json
from myreq import myAgent, myIPs
from lxml import etree


def city_json(text):
    """
    解析城市的json
    :param text: 网页源码
    :return: {城市：城市拼音}的列表
    """
    print('正在获取城市列表')
    j = json.loads(text)
    city_list = []
    all_city = j['data']['cityList']['all']
    for k in sorted(all_city):
        for i in all_city[k]:
            city_list.append({i['name']: i['domain']})
    print('城市列表获取成功')
    return city_list


def ctx_call(args):
    """
    调用js函数, 执行js函数, *****注意: 这里存在js安全性未知问题*****
    :param args: 传入计算antipas的两个参数的元组, 在后面用序列解包
    :return: 返回的是计算结果
    """
    with open('antipas/antipas.js') as f:
        js_file = f.read()
    ctx = execjs.compile(js_file)
    return ctx.call('anti', *args)


class Antipas:
    """
    这个类包含了解析反爬页, 车辆链接, 车辆信息的各种方法
    都要用到cookie: antipas
    """
    proxy_iter = myIPs.proxy_iter()  # 一个生成器

    def __init__(self, the_url='https://www.guazi.com/www/buy', sleeptime=4, timeout=5, retry_times=5):
        self.url = the_url
        self.sleeptime = sleeptime
        self.timeout = timeout
        self.retry_times = retry_times

    def with_antipas(self):
        """
        设置头部信息, 代理
        两次请求: 第一次没有带cookie, 解析页面获得antipas, 并将其添加到cookies中, 发送第二次请求
        捕捉两次请求的异常
        :return: 返回的是第二次请求后解析后的文本, 或者是None
        """
        time.sleep(random.randint(1, self.sleeptime))
        proxy = next(Antipas.proxy_iter)
        agent = myAgent.get_agent()
        headers = {'User-Agent': agent, 'Host': 'www.guazi.com'}
        proxies = {'https': proxy[0] + ':' + proxy[1]}
        try:
            with requests.get(
                    self.url, headers=headers, timeout=self.timeout, proxies=proxies
            ) as response:
                text = response.content.decode(encoding='utf-8')
            match = re.search(r'(?<=value=anti\(\')(.*?=)\',\'(\d.*?)\'\)', text, re.S)
            if match:
                antipas = ctx_call(match.groups())  # 获得antipas
                cookies = {'antipas': antipas}  # antipas添加到cookies中
                with requests.get(
                        self.url, headers=headers, cookies=cookies,
                        proxies=proxies, timeout=self.timeout
                ) as ne:
                    return ne.text
        except socket.timeout as e:
            print(e)
        except requests.exceptions.ConnectTimeout as e:
            print(e)
        except requests.exceptions.ConnectionError as e:
            print(e)
        finally:
            print('{}...'.format(str(proxy)))

    def check_text(self, pa):
        """
        检查网页是否是想要的, 重复self.retry_times 次, IP也同时更换
        res1 解析成功
        res2 链接无效
        res3 还是在反爬页
        其它情况...
        :param pa: 正则表达式
        :return: 匹配成功返回的是解析后的文本, 否则返回None
        """
        flag = self.retry_times
        while flag:
            text = self.with_antipas()
            if not text:
                print('网络问题?')
                continue
            res1 = re.search(pa, text, re.S)
            res2 = re.search(r'<title>【您访问的页面不存在】-瓜子二手车直卖网</title>', text)
            res3 = re.search(r'(?<=value=anti\(\')(.*?=)\',\'(\d.*?)\'\)', text, re.S)
            if res1:
                print('解析成功', self.url)
                return text
            if res2:
                print('页面不存在', self.url)
                break
            if res3 and flag > 1:
                print('再次获取antipas中....')
                continue
            if res3 and flag == 1:
                print('我已经尽力了, 不过还没有获取有效的antipas', self.url)
                break  # 不去执行循环外的else
            flag -= 1  # 没有想要的结果尝试下一次
        else:  # 其它情况...
            print('这是什么链接?', self.url)

    def get_city_name(self):
        """
        这里要发送三次请求
        第一次获得antipas
        第二次请求主网址
        第三次请求网站的ajax获得城市的json数据
        解析页面, 获得城市的汉语和拼音缩写
        :return: [{城市：拼音},...]
        """
        www_url = 'https://www.guazi.com/www/'
        headers = {'User-Agent': myAgent.get_agent(), 'Host': 'www.guazi.com'}
        while 1:
            with requests.session() as s:
                s.headers.update(headers)
                text = s.get(www_url, timeout=self.timeout).text
                match = re.search(r'(?<=value=anti\(\')(.*?=)\',\'(\d.*?)\'\)', text, re.S)
                antipas = ctx_call(match.groups())
                s.cookies.update({'antipas': antipas})
                s.get(www_url, timeout=self.timeout)
                # print(t.text)
                s.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
                s.headers['X-Requested-With'] = 'XMLHttpRequest'
                s.headers['Referer'] = 'https://www.guazi.com/www/'
                ajax_url = www_url + '?act=ajaxGetOpenCity'
                time.sleep(1)
                city_text = s.get(ajax_url, timeout=self.timeout).text
                if city_text:
                    return city_json(city_text)

    def get_max_page(self):
        """
        解析页面找出最大页
        :return: 最大页, 或者是1
        """
        pa = r'class="list-filter".+全部.+付三成.+保卖车'
        text = self.check_text(pa)
        if text:
            page_box = re.search(r'class="pageBox".+?下一页', text, re.S)
            if page_box:
                max_page = re.findall(r'<span>(\d+)</span>', page_box.group(), re.S)[-1]
                return int(max_page)
            else:
                return 1

    def get_links(self):
        """
        解析页面获得多个车辆的链接
        :return: 返回包含多个车辆的链接的列表, 或则是None
        """
        pa = r'class="list-filter".+全部.+付三成.+保卖车'
        text = self.check_text(pa)
        if text:
            pa_link = re.compile(r'a title=.+?href=\"(.+?)\"')
            car_links = pa_link.findall(text)
            if car_links:
                return car_links

    def get_info(self):
        """
        解析页面获得这辆车辆的信息
        :return: 包含信息的列表, 或者是None
        """
        pa = r'上牌时间.+表显里程.+上牌地'
        text = self.check_text(pa)
        if text:
            html = etree.HTML(text)
            city = html.xpath('//*[@class="city-curr"]/text()')[0].strip()
            price = html.xpath('//*[@class="pricestype"]/text()')[0].strip().replace('¥', '') + '万'
            newcarprice = html.xpath('//*[@class="newcarprice"]/text()')[0].strip()
            titlebox = html.xpath('//*[@class="titlebox"]/text()')[0].strip()
            one = html.xpath('//*[@class="one"]/div[1]/text()')[0].strip()
            two = html.xpath('//*[@class="two"]/div[1]/text()')[0].strip()
            three = html.xpath('//*[@class="three"]/div[1]/text()')[0].strip()
            four = html.xpath('//*[@class="four"]/div[1]/text()')[0].strip()
            five = html.xpath('//*[@class="five"]/div[1]/text()')[0].strip()
            six = html.xpath('//*[@class="six"]/div[1]/text()')[0].strip()
            seven = html.xpath('//*[@class="seven"]/div[1]/text()')[0].strip()
            eight = html.xpath('//*[@class="eight"]/div[1]/text()')[0].strip()
            nine = html.xpath('//*[@class="nine"]/div[1]/text()')[0].strip()
            ten = html.xpath('//*[@class="ten"]/div[1]/text()')[0].strip()
            last = html.xpath('//*[@class="last"]/div[1]/text()')[0].strip()
            manufacturer = html.xpath(
                '//*[@class="detailcontent clearfix js-detailcontent active"]/table//tr/td[2]/text()'
            )[0].strip()
            model = html.xpath(
                '//*[@class="detailcontent clearfix js-detailcontent active"]/table//tr[3]/td[2]/text()'
            )[0].strip()
            engine = html.xpath(
                '//*[@class="detailcontent clearfix js-detailcontent active"]/table//tr[4]/td[2]/text()'
            )[0].strip()
            _id = html.xpath('//*[@class="right-carnumber"]/text()')[0].strip()[4:]
            car_info = [city, price, newcarprice, titlebox, one, two, three, four, five, six, seven, eight, nine, ten,
                        last,
                        manufacturer,
                        model, engine, _id]
            if car_info:
                return car_info


if __name__ == '__main__':
    url = 'https://www.guazi.com/su/buy'
    # ips = ['120.27.147.1', '118.193.107.222', '120.27.230.68', '118.193.107.175', '123.56.92.104', '39.134.161.18']
    p = Antipas(url)
    print(p.get_max_page())
    # 或者是一个车辆信息页的链接 https://www.guazi.com/su/236f78c93a5908b1x.htm#fr_page=list&fr_pos=city&fr_no=34
    # print(p.get_info())
