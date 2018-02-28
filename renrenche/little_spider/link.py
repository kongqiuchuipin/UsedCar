# _*_ coding:utf-8 _*_
"""
单个城市的车辆链接采集
小于50页，翻页采集
大于50页，按照价格分类采集
"""
import requests
import re
import time
import random
import socket
from req_used import myAgent, myIPs
from little_spider.shelve_action import shelve_update
from lxml import etree


def id_add_url(_id, city_name):
    return {'https://www.renrenche.com/' + city_name + '/car/' + i for i in _id}


class Link:
    proxy_iter = myIPs.proxy_iter()

    def __init__(self, city_name, timeout=5, sleeptime=1):
        self.base_url = 'https://www.renrenche.com/'
        self.city_name = city_name
        self.city_url = self.base_url + self.city_name + '/ershouche/'
        self.timeout = timeout
        self.sleeptime = sleeptime
        self.first_page_flag = False  # 仅在解析第一页时打开
        self.max_page = 1
        self.price_url_list = []

    def request_url(self, page_url):
        time.sleep(random.randint(self.sleeptime, self.sleeptime + 5))
        proxy = next(Link.proxy_iter)
        headers = {'User-Agent': myAgent.get_agent(),
                   'Host': 'www.renrenche.com'}
        proxies = {'http': proxy[0] + ':' + proxy[1],
                   'https': proxy[0] + ':' + proxy[1]}
        print('{}'.format(str(proxy)), '发送请求 ...')
        try:
            with requests.session() as session:
                session.headers.update(headers)
                session.headers.update(proxies)
                request = session.get(page_url, timeout=self.timeout)
                text = request.text
            return text
        except socket.timeout as e:
            print(e)
        except requests.ConnectionError as e:
            print(e)
        except Exception as e:
            print(e)

    def check(self, text):
        if text:
            se = re.search('价格最高.+价格最低.+最新发布', text, re.S)
            if se:
                return True
            print(text)

    def in_one_page_links(self, page_url):  # 获得最大页数和第一页的链接
        print(page_url)
        while 1:
            text = self.request_url(page_url)
            if self.check(text):
                break
        html_text = etree.HTML(text)
        xpath = html_text.xpath('//li[@class="span6 list-item car-item"]/a/@data-car-id')
        car_ids = set(xpath)
        shelve_update('all_link', id_add_url(car_ids, self.city_name))
        if not self.first_page_flag:  # 找出最大页
            self.max_page = self.get_max_page(html_text)
            if self.max_page >= 50 and 'ershouche/pr' not in page_url:  # 如果在城市链接页，最大页数大于50页，获得价格分类链接
                self.price_url_list = self.price_list(html_text)
        self.first_page_flag = True

    def price_list(self, html_text):
        filter_price = html_text.xpath('//ul[@id="filter_price"]//a/@href')
        price_url_list = filter_price[1:]
        return price_url_list

    def get_max_page(self, html_text):
        num_list = html_text.xpath('//ul[@class="pagination js-pagination"]//a/text()')
        if num_list:
            max_page = max([int(i) for i in num_list])
        else:
            max_page = 1
        return max_page

    def simple_way(self, page_url, page_num):
        while page_num < self.max_page:
            page_num += 1
            p_url = page_url + 'p{}'.format(page_num)
            self.in_one_page_links(p_url)

    def hard_way(self):
        for url in self.price_url_list:
            self.first_page_flag = False
            pr_url = self.base_url + url[1:]
            self.simple_way(pr_url, 0)

    def get_city_links(self):
        self.in_one_page_links(self.city_url)
        if self.max_page < 50:
            print('A计划'.center(40, '.'))
            self.simple_way(self.city_url, 1)
        else:
            print('B计划'.center(40, '.'))
            self.hard_way()


if __name__ == '__main__':
    s = Link('dl')
    s.get_city_links()
