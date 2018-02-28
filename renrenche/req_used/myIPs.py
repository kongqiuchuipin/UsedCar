# _*_ coding:utf-8 _*_
import random
import pymongo


def proxy_set():
    """
    集合
    """
    client = pymongo.MongoClient()
    db = client['MyIPs']
    collection = db['tested']
    proxies = {tuple((tup['ip'], tup['port'], tup['form'])) for tup in collection.find()}
    return proxies


def proxy_iter():
    """
    ip生成器
    """
    index = 0
    proxies = list(proxy_set())
    random.shuffle(proxies)
    while 1:
        ip = proxies[index]
        yield ip
        index += 1
        if index == len(proxies):
            index = 0


if __name__ == '__main__':
    print(proxy_set())
    x = proxy_iter()
    for i in range(2000):
        print(next(x))
