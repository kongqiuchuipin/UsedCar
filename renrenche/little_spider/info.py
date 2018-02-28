# _*_ coding:utf-8 _*_
import requests
import re
import pymongo
import time
import random
from req_used import myAgent, myIPs
from little_spider.shelve_action import shelve_open, shelve_add
from lxml import etree

collection = pymongo.MongoClient()['renrenChe']['all']

proxy_iter = myIPs.proxy_iter()


def request_url(page_url, sleeptime=1):
    time.sleep(random.randint(sleeptime, sleeptime + 5))
    proxy = next(proxy_iter)
    headers = {'User-Agent': myAgent.get_agent(),
               'Host': 'www.renrenche.com'}
    proxies = {'http': proxy[0] + ':' + proxy[1],
               'https': proxy[0] + ':' + proxy[1]}
    print('{}'.format(str(proxy)), '发送请求 ...', page_url)
    try:
        with requests.get(page_url,headers=headers, proxies=proxies, timeout=6.66) as req:
            text = req.text
        return text
    except Exception as e:
        print(e)


def parse_pgae(text):
    html = etree.HTML(text)
    title = html.xpath('//*[@id="basic"]//h1[@class="title-name"]/text()')[0]
    _id = html.xpath('//*[@id="basic"]//p[@class="detail-car-id"]/text()')[0].strip()[4:]
    location = html.xpath('//*[@id="report"]/div/div/p/span[2]/text()')[0][5:]
    price = html.xpath('//*[@id="basic"]//p[@class="price detail-title-right-tagP"]/text()')[0][1:]
    new_car_price = html.xpath('//*[@id="basic"]//div[@class="new-car-price detail-title-right-tagP"]/span/text()')[
        0]
    time1 = html.xpath('//*[@id="report"]/div/div/div[2]/table//tr[2]/td[2]/text()')[0]
    distance = html.xpath('//ul[@class="row-fluid list-unstyled box-list-primary-detail"]/li[2]/div/p[1]/strong/text()'
                          )[0]
    standard = html.xpath('//p[@class="detail-version3-right-icon"]/strong/text()')[0]
    cc = html.xpath('//li[@class="span displacement"]/div/strong/text()')[0]
    color = html.xpath('//*[@id="report"]/div/div/div[2]/table//tr[1]/td[2]/text()')[0]
    nian_iian = html.xpath('//*[@id="report"]/div/div/div[2]/table//tr[1]/td[4]/text()')[0]
    bao_xian = html.xpath('//*[@id="report"]/div/div/div[2]/table//tr[1]/td[6]/text()')[0]
    guo_hu = html.xpath('//*[@id="report"]/div/div/div[2]/table//tr[2]/td[8]/text()')[0]
    style = html.xpath('//*[@id="basic-parms"]//tr[2]/td[1]/div[2]/text()')[0].strip()
    engine = html.xpath('//*[@id="basic-parms"]//tr[3]/td[1]/div[2]/text()')[0].strip()
    manufacturer = html.xpath('//*[@id="basic-parms"]//tr[2]/td[3]/div[2]/text()')[0].strip()
    link = 'https://www.renrenche.com' + html.xpath('//*[@id="basic"]/div[1]/p/a[5]/@href')[0]
    bian_su_xiang = html.xpath('//*[@id="basic-parms"]//tr[3]/td[2]/div[2]/text()')[0].strip()
    doc = {'名称': title, '车源号': _id, '地区': location, '价格': price, '新车价格': new_car_price, '上牌日期': time1,
           '表显里程': distance, '排放标准': standard, '排量': cc, '颜色': color, '年检到期': nian_iian, '链接': link,
           '保险到期': bao_xian, '过户次数': guo_hu, '车型': style, '发动机': engine, '生产厂商': manufacturer,
           '变速箱': bian_su_xiang}
    return doc


class Info:
    def __init__(self, link):
        self.link = link
        self.flag = False

    def get(self, times=5):
        while times:
            text = request_url(self.link)
            self.check_text(text)
            if self.flag:
                doc = parse_pgae(text)
                self.roll_to_db(doc)
                break
            times -= 1
        else:
            shelve_add('invalid_link', self.link)

    def roll_to_db(self, doc):
        condition = {'车源号': doc['车源号']}
        if collection.find_one(condition):
            print('已经有重复', condition)
            shelve_add('repeat_link', self.link)
        else:
            collection.insert_one(doc)
            print('录入成功', condition)

    def check_text(self, text):
        self.flag = False
        if text:
            if re.search('这个页面开车离开网站了', text):
                print('页面不存在')
                shelve_add('invalid_link', self.link)
            elif re.search('<div class="sold-out-tips">已下架</div>', text):
                print('已下架')
                shelve_add('invalid_link', self.link)
            elif re.search('上牌时间.+公里数.+排量', text, re.S):
                print('正在获取车辆信息')
                self.flag = True
            else:
                print('这是什么链接?')
        else:
            print('获取网页失败')


def for_catch_link():
    """
    对本地数据筛选
    :return: 要采集的车辆链接的集合
    """
    all_link = shelve_open('all_link')
    invalid_link = set(shelve_open('invalid_link'))
    repeat_link = set(shelve_open('repeat_link'))
    in_database_link = {i['链接'] for i in collection.find()}
    for_catch_links = all_link - in_database_link - invalid_link - repeat_link
    print('数据库{}条, 待采集{}条'.format(len(in_database_link), len(for_catch_links)))
    return for_catch_links


def info():
    for_catch_links = for_catch_link()
    for link in for_catch_links:
        act = Info(link)
        act.get()


if __name__ == '__main__':
    info()
