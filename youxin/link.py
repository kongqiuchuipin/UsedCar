# _*_ coding:utf-8 _*_
"""
采集单个城市内所有车辆链接的类Link的方法get_links:
由于主网站最多显示50页, 所以通过从每个城市的浏览页面开始采集链接,
对于单个城市总页面超过五十页的, 按照价格分类再细分采集
"""
import requests
import re
import socket
import json
from bs4 import BeautifulSoup
from useragent_and_proxies.myAgent import get_agent
from useragent_and_proxies.myIPs import proxy_iter
from shelve_method_ import shelve_add

proxies_iter = proxy_iter()


def get_page(url):
    """
    发送请求, 得到网页
    :param url: 单个城市页面或者按照价格分类的页面
    :return: 网页文本字符串
    """
    print('request'.center(20, '.'))
    proxy = next(proxies_iter)
    headers = {'User-Agent': get_agent(),
               'Referer': 'https://www.xin.com/beijing/s',
               'Host': 'www.xin.com'}
    proxies = {'https': proxy[0] + ':' + proxy[1]}
    try:
        with requests.get(url, headers=headers, proxies=proxies, timeout=5) as req:
            text = req.text
        return text
    except socket.timeout as e:
        print(e)
    except requests.exceptions.ConnectionError as e:
        print(e)
    except requests.exceptions.ReadTimeout as e:
        print(e)


def get_all_city_name():
    """
    打印城市名和拼音缩写
    :return:  包含城市拼音缩写的列表
    """
    url = 'https://www.xin.com/shanghai/s/'
    text = get_page(url)
    res = []
    print('获得城市名称列表:')
    s = re.search('var city_all = (.+?)var hot_city', text, re.S).group(1)
    city_json = json.loads(s.strip()[:-1])
    for _id in city_json:
        res.append([city_json[_id]['ename'], city_json[_id]['cityname']])
    res.sort()
    for c in res:
        print(c)
    return [i[0] for i in res]


class Link:
    def __init__(self, city_name='beijing', sleeptime=10):
        self.max_page = 0
        self.page_nums = 0
        self.city_name = city_name
        self.price_kinds_url = []
        self.sleeptime = sleeptime

    def get_max(self, b_text):
        """
        获得最大页数
        获得车源数量,因为每个城市浏览页只给出了50页, 即2000个链接
        获得价格搜索条件列表
        :param b_text: BeautifulSoup实例
        :return: None
        """
        price_bs4 = BeautifulSoup(str(b_text.find('dl', id='select3')), 'lxml')
        page_list = [int(i.get('data-page')) for i in b_text.find_all('a', attrs={'name': 'view_i'})]
        if page_list:  # 超过一页
            self.max_page = max(page_list)
            self.price_kinds_url = [i.get('href')[:-1] for i in price_bs4.find_all('a')[1:]]
            page_nums = b_text.find('a', class_='view_v active')
            if page_nums:  # 车源数量
                self.page_nums = int(page_nums.get_text().replace('全部车源(', '').replace(')', ''))
        else:
            self.max_page = 1

    def in_one_page_links(self, page_url):
        """
        采集一个页面内的所有车辆的链接
        :param page_url: 带采集页
        :return: 包含了车辆链接的集合
        """
        while 1:
            text = get_page(page_url)
            if text:
                check = re.search('没有找到您想要的爱车，建议您减少筛选条件试试', text)  # 城市没有二手车辆
                if check:
                    print(self.city_name, '城市没有二手车辆 ...')
                    break
                b_text = BeautifulSoup(text, 'lxml')
                if not self.max_page:  # 只获得一次最大页
                    self.get_max(b_text)
                    print('{}, 共{}页'.format(page_url[:-3], self.max_page))
                b = b_text.find_all(class_='_list-con list-con clearfix ab_carlist')
                c_text = BeautifulSoup(str(b[0]), 'lxml')
                find_links = c_text.find_all('a', attrs={'class': 'tit yx-l2'})
                res = {i.get('href')[2:] for i in find_links}
                return res

    def get_links(self):
        """
        单个城市采集器, shelve保存
        :return: None
        """
        link_collect = set()
        page_num = 0
        plan_flag = True
        while 1:  # 翻页
            page_num += 1
            page_url = 'https://www.xin.com/{}/i{}/'.format(self.city_name, page_num)
            in_page_links = self.in_one_page_links(page_url)
            if not in_page_links:
                break
            new_links = set(in_page_links) - link_collect
            if not new_links:
                break
            if self.page_nums <= 2000:  # 如果车源数量小于等于2000, 按照页数顺序采集
                if plan_flag:
                    print('A计划'.center(30, '*'))
                    plan_flag = False
                link_collect.update(new_links)
                new_num = len(new_links)
                tot_num = len(link_collect)
                for l in new_links:
                    shelve_add('all_link', l)
                print('{}采集完成, 获得了{}个新链接, 共{}条链接'.format(page_url, new_num, tot_num))
                if page_num >= self.max_page:
                    break
            elif self.page_nums > 2000:  # 如果车源数量大于等于2000, 按照价格分类来采集
                print('B计划'.center(30, '*'))
                self.get_links_another_way()
                break
        print('{} 完成, 共{}条'.format(self.city_name, len(link_collect)).center(30, '*') + '\n')

    def get_links_another_way(self):
        """
        按照价格分类的采集
        :return: None
        """
        link_collect = set()
        for url in self.price_kinds_url:
            page_num = 0
            self.max_page = 0  # 重置最大页数
            while 1:  # 翻页
                page_num += 1
                page_url = 'https:' + url + '/i{}'.format(page_num)
                new_links = set(self.in_one_page_links(page_url)) - link_collect
                link_collect.update(new_links)
                new_num = len(new_links)
                tot_num = len(link_collect)
                for l in new_links:
                    shelve_add('all_link', l)
                print('{}采集完成, 获得了{}个新链接, 共{}条链接'.format(page_url, new_num, tot_num))
                if page_num >= self.max_page:
                    break


if __name__ == '__main__':
    link = Link('shanghai')
    print(link.get_links())
