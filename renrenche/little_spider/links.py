# _*_ coding:utf-8 _*_
import requests
import shelve
from req_used import myAgent
from lxml import etree
from little_spider.link import Link
from little_spider.shelve_action import shelve_add

"""
采集所有的城市的链接
"""


def city_short_name():
    try:
        with shelve.open('data/city') as db:
            couple = db['city_short_name']
    except KeyError:
        url = 'https://www.renrenche.com/bj/ershouche'
        agent = myAgent.get_agent()
        headers = {'User-Agent': agent}
        response = requests.get(url, headers=headers, timeout=7)
        text = response.text
        html = etree.HTML(text)
        name = html.xpath('//div[@class="area-city-letter"]//a[@class="province-item "]/text()')
        hrefs = html.xpath('//div[@class="area-city-letter"]//a[@class="province-item "]/@href')
        lessen = lambda href: [l[1:-1] for l in href]
        couple = [(str(k), str(v)) for k, v in zip(name, lessen(hrefs))]
        with shelve.open('data/city') as db:
            db['city_short_name'] = couple
    return couple


def link():
    names = city_short_name()
    try:
        with shelve.open('data/city') as she:
            done_city_link = she['city_done_link']
    except KeyError:
        done_city_link = set()
    for name, ename in names:
        if name not in done_city_link:
            print(name, '开始采集')
            spider = Link(ename)
            spider.get_city_links()
            shelve_add('city_done_link', name)
            print(name, '已经完成')


if __name__ == '__main__':
    link()
