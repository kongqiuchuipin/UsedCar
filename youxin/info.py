# _*_ coding:utf-8 _*_
"""
采集单个车辆信息的函数info
"""

import requests
import re
import socket
from bs4 import BeautifulSoup
from lxml import etree
from useragent_and_proxies.myAgent import get_agent
from useragent_and_proxies.myIPs import proxy_iter
from shelve_method_ import shelve_add

proxies_iter = proxy_iter()


def get_page(link):  # 返回.text
    print('request'.center(20, '.'))
    car_url = 'https://' + link
    city_url = 'https://' + link[:-17] + '/s'
    proxy = next(proxies_iter)
    headers = {'User-Agent': get_agent(),
               'Referer': 'https://www.xin.com/beijing/s/',
               'Host': 'www.xin.com'}
    proxies = {'https': proxy[0] + ':' + proxy[1]}
    try:
        with requests.session() as session:  # 通过session保持, 首先打开地区浏览页,再打开车辆信息页, 不然会会被反爬转到验证页
            session.headers.update(headers)
            session.proxies.update(proxies)
            session.get(city_url, timeout=5)
            two = session.get(car_url)
            return two.text
    except socket.timeout as e:
        print(e)
    except requests.ConnectTimeout as e:
        print(e)
    except Exception as e:
        print(e)


def info(link):  # 获得的文本可能出现, 链接不存在, 或者出现其它情况
    while 1:  # 这里设置无限次
        text = get_page(link)
        if text:  # 车辆信息页有两种排版方式
            check1 = re.search('使用性质.+?年检到期.+?保险到期', text, re.S)  # 新版
            check2 = re.search('表显里程.+?排量.+?所在城市', text, re.S)  # 旧版
            check3 = re.search('主人，这个页面找不到啦', text, re.S)  # 车辆链接不存在的
            if check1:
                print('获得了车辆信息', link)
                return my_parse1(text, link)
            if check2:
                print('获得了车辆信息', link)
                return my_parse2(text, link)
            if check3:
                print('页面不存在', link)
                shelve_add('invalid_link', link)
                break
        else:
            print('...再次尝试', link)
            pass


def my_parse1(text, link):  # 新版
    b = BeautifulSoup(text, 'lxml')
    name = b.find(class_='cd_m_h_tit').get_text(strip=True)
    price = b.find(class_='cd_m_info_jg').get_text(strip=True)[1:]
    new_car_price = b.find(class_='new-noline').get_text(strip=True)
    mmp = [i.get_text(strip=True) for i in b.find_all(class_='cd_m_desc_val')][1:]
    info1 = [i.get_text(strip=True) for i in b.find_all(class_='cd_m_desc_key')][0]
    car_id = b.find(class_='cd_m_info_cover_carid').get_text(strip=True)
    info2 = [i.get_text(strip=True) for i in b.find_all(class_='cd_m_i_pz_val')]
    doc = {'品牌': name, '价格': price, '新车价格': new_car_price, '里程': mmp[0], '排放标准': mmp[1],
           '排量': mmp[2], '地区': mmp[3], '上牌时间': '{}-{}'.format(info1[:4], info1[5:7]), '车型': info2[9],
           '链接': 'https://' + link, '网站编号': car_id, '年检到期': info2[3], '颜色': info2[8],
           '保险到期': info2[4], '生产厂商': info2[6], '发动机': info2[12], '变速箱': info2[13]}
    return doc


def my_parse2(text, link):  # 旧版
    b = BeautifulSoup(text, 'lxml')
    name = b.find(class_='d-tit').get_text(strip=True)
    price = b.find(class_='wan_1').get_text(strip=True)[1:]
    new_car_price = b.find(class_='wan_2').get_text(strip=True)
    b0 = BeautifulSoup(str(b.find(class_='contit')), 'lxml')
    em = [i.get_text(strip=True) for i in b0.find_all('em')]
    car_id = b.find(class_='vin_num').get_text(strip=True)
    lxml = etree.HTML(text)
    manufacturer = lxml.xpath('//div[@class="param clearfix"]/div[2]/table//tr[6]/td[2]/text()')[0]
    emission_standards = lxml.xpath('//div[@class="param clearfix"]/div[1]/table//tr[1]/td[2]/text()')[0]
    nian_jian = lxml.xpath('//div[@class="param clearfix"]/div[1]/table//tr[5]/td[2]/text()')[0]
    bao_xian = lxml.xpath('//div[@class="param clearfix"]/div[1]/table//tr[4]/td[2]/text()')[0]
    color = lxml.xpath('//div[@class="param clearfix"]/div[2]/table//tr[2]/td[2]/text()')[0]
    che_xin = lxml.xpath('//div[@id="ulover"]/div[2]/div[2]/table//tr[2]/td[2]/text()')[0]
    bian_su_xiang = lxml.xpath('//*[@id="ulover"]/div[5]/div[1]/table//tr[1]/td[2]/text()')[0]
    engine = lxml.xpath('//*[@id="ulover"]/div[3]/div[1]/table//tr[1]/td[2]/text()')[0]
    doc = {'名称': name, '价格': price, '新车价格': new_car_price, '排放标准': emission_standards,
           '排量': em[3], '地区': em[4], '上牌时间': em[1], '车型': che_xin, '里程': em[2],
           '链接': 'https://' + link, '网站编号': car_id, '年检到期': nian_jian, '颜色': color,
           '保险到期': bao_xian, '生产厂商': manufacturer, '发动机': engine, '变速箱': bian_su_xiang}
    return doc
