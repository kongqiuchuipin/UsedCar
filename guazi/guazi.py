# _*_ coding:utf-8 _*_
"""

控制器: 包括了调节抓取的内容, 信息. 数据库和文件的读写
"""
import shelve
from antipas import catch_page
from pymongo import MongoClient
import os
import re


def shelve_save(key, values):
    with shelve.open('data/data') as she:
        if key in she.keys() and she[key]:
            s = she[key]
            bef = len(s)
            s.update(values)
            aft = len(s)
            she[key] = s
            print('更新了{}, 共{}条'.format(aft-bef, aft))
        else:
            she[key] = values


def shelve_open(key):
    with shelve.open('data/data') as she:
        if key in she.keys():
            return she[key]
        else:
            return set()


def simple_link(link):
    """
    /su/9da3a7292bf4dd04x.htm 保存成类似这样的, 方便删选, 防止有的同一款车有不同网址
    """
    linked = link.replace('https://www.guazi.com', '')
    pa = re.compile('.+?htm')
    se = pa.search(linked)
    if se:
        res = se.group()
        return res


# def get_city():
#     """
#     获得所有城市的中文和拼音
#     """
#     big = catch_page.Antipas()
#     names = big.get_city_name()
#     with open('data/city_name', 'w', encoding='utf-8') as f:
#         for i in names:
#             f.write(str(i) + '\n')
#     # print(names)
#     return names


class CarUsed:
    """
    瓜子二手车采集器, city_name是地区城市简写（参照官网）, 这里用地区做分类分别保存到不同的数据库中, 待处理分析或者以后合并
    """

    def __init__(self, city_name='www'):  # www是全国
        self.base_url = 'https://www.guazi.com'
        self.city_name = city_name
        self.begin_page = 1
        self.end_page = 0
        # 当前要采集的次数（由于刷新网页包含的车辆不同, 所以设置每页的采集次数）
        self.tot_catch_times = 0  # 如果没有缓存默认是0
        self.cache_filename = 'data/' + self.city_name + '_cache'  # 采集器上次采集的信息的文件, 包含次数和页数
        client = MongoClient()
        db = client['guaZi']
        self.collection = db[city_name]  # 数据库名称以城市命名
        self.links_in_database = {simple_link(l['链接']) for l in self.collection.find()}

    def read_cache(self):
        """
        导入缓存如果有的话, 读取数据库信息
        """
        try:
            with open(self.cache_filename, encoding='utf-8') as cache_file:
                text = cache_file.read().strip()
            print('导入缓存成功')
            ex = {}
            exec(text, {}, ex)  # 调用缓存
            self.begin_page = ex['last_page'] + 1
            self.tot_catch_times = ex['tot_catch_times'] - 1  # 采集次数统计
            print('上次采集到{}页, 采集完成了{}次'.format(self.begin_page, self.tot_catch_times))
        except FileNotFoundError:
            print('没有缓存信息文件')

    def catch_links(self, begin_page=None, end_page=None, catch_times: int = 1):
        """
        抓取网页内的车辆链接
        """
        self.read_cache()
        base_links_url = self.base_url + '/' + self.city_name + '/buy'
        now_catch_times = catch_times  # 重复采集, 没有传入的话, 默认3次
        self.begin_page = begin_page if begin_page else self.begin_page  # 如果没有传入参数则从缓存里取出或者是默认
        self.end_page = end_page if end_page else self.end_page
        while not self.end_page:  # 如果没有传入最大页数, 通过解析网页得到
            self.end_page = catch_page.Antipas(base_links_url).get_max_page()
        # 重复采集器 ----------------------------------------------------------
        for time in range(now_catch_times):  # time =0, 1, 2...
            if os.path.exists(self.cache_filename):  # 缓存文件
                now_bananas = self.tot_catch_times + time + 1  # 当前的采集次数
            else:
                now_bananas = 1  # 变量仅仅为了计数
            print('>>>>> 第{}次采集 <<<<<'.format(now_bananas).center(100, '-'))
            print('采集页数:', self.end_page)
            # 翻页采集器 -------------------------------------------------------
            while self.begin_page <= self.end_page:
                links_url = base_links_url + '/o{}/#bread'.format(self.begin_page)
                links_antipas = catch_page.Antipas(links_url)
                print('采集车辆链接')
                page_links = links_antipas.get_links()
                simple_page_links = set([simple_link(l) for l in page_links])
                # 写入缓存 ---------------------------------------------------------------------------------
                with open(self.cache_filename, 'w', encoding='utf-8') as file:
                    file.write('last_page = {}\ntot_catch_times = {}'.format(self.begin_page, now_bananas))
                shelve_save('all_link', simple_page_links)
                self.begin_page += 1  # 如果采集成功, 则采集下一页
            print('>>>>>第{}次采集已完成<<<<<'.format(now_bananas).center(100, '-'))
            self.begin_page = 1  # 重置网址, 完成多次采集

    def for_catch_link(self):
        print('数据库{}条链接'.format(len(self.links_in_database)))
        all_links = shelve_open('all_link')
        invalid_links = shelve_open('invalid_link')
        repeat_links = shelve_open('repeat_link')
        for_catch_links = all_links - self.links_in_database - invalid_links - repeat_links  # 减去已经有
        print('{}条链接待采集'.format(len(for_catch_links)))
        return for_catch_links

    def catch_info(self):
        """
        对数据库和采集器内的所有链接进行筛选采集
        """
        for_catch_links = self.for_catch_link()
        print('开始采集车辆信息:'.center(100, '*'))
        new = 0
        repeat = 0
        while for_catch_links:
            car_link = 'https://www.guazi.com' + for_catch_links.pop()
            info_antipas = catch_page.Antipas(car_link)
            info = info_antipas.get_info()
            if info:
                doc = {
                    '地区': info[0], '价格': info[1], '新车价格': info[2], '名称': info[3], '上牌时间': info[4],
                    '表显里程': info[5], '上牌地': info[6], '排放标准': info[7], '变速箱': info[8], '排量': info[9],
                    '过户次数': info[10], '看车地址': info[11], '年检到期': info[12], '交强险': info[13],
                    '商业险到期': info[14], '生产厂商': info[15], '车型': info[16], '发动机': info[17],
                    '车源号': info[18], '链接': car_link
                }
                self.collection.ensure_index('车源号')  # 设置索引
                _id = self.collection.find_one({'车源号': info[18]})
                if not _id:
                    self.collection.insert_one(doc)  # 按车源号去重
                    new += 1
                    print('录入成功:', info[3], '车源号:', info[18])
                else:
                    # collection.find_one_and_update({'车源号': info[18]}, {'$set': doc})
                    repeat += 1
                    print('已有重复:', info[3], '车源号:', info[18])
                    shelve_save('repeat_link', {car_link})
                    break  # 采集成功换另一个链接------------------------------------------------------------
            else:  # 无效的链接保存到文件
                shelve_save('invalid_link', {car_link})
                print('XXXXX 无效的链接 XXXXX')
        print('车辆信息录入完成：新增{}条, 重复{}条'.format(new, repeat).center(100, '*'))


if __name__ == '__main__':
    spider = CarUsed()
    # spider.catch_links(1)
    spider.catch_info()
