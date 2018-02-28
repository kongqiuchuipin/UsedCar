# _*_ coding:utf-8 _*_


from link import Link, get_all_city_name
from info import info
from pymongo import MongoClient
from shelve_method_ import shelve_open, shelve_add, shelve_save


def all_city_links():
    all_city = shelve_open('all_city_name')  # 如果已经有城市列表
    if not all_city:
        all_city = get_all_city_name()  # 如果没有
        shelve_save('all_city_name', all_city)
    return all_city


def get_link():
    all_city = all_city_links()
    done = shelve_open('city_done_link')  # 采集过的
    doing = [i for i in all_city if i not in done]
    for city in doing:
        if city not in done:  # 未采集的
            link_spider = Link(city)
            link_spider.get_links()
            shelve_add('city_done_link', city)  # 在这里设置记录, 下一次采集在这之后


def get_info():  # 针对全部城市的采集
    collection = MongoClient()['youXin']['all']
    city_links = set(shelve_open('all_link'))
    city_invalid_links = set(shelve_open('invalid_link'))
    if city_links:  # 如果文件里存在链接
        in_database = {i['链接'][8:] for i in collection.find()}
        l_i_d = len(in_database)
        link_for_catch = city_links - in_database - city_invalid_links
        l_f_c = len(link_for_catch)
        print('数据库:{}, 待采集{}, 共{}条'.format(l_i_d, l_f_c, l_i_d + l_f_c))
        for i, link in enumerate(link_for_catch):
            print(i + l_i_d, 'of', l_i_d + l_f_c)  # # 页面不存在这种情况也计算在内
            doc = info(link)
            if doc:
                collection.insert_one(doc)
        print('完成'.center(30, '*'))


if __name__ == '__main__':
    # get_link()
    get_info()
