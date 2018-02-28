# _*_ coding:utf-8 _*_

import shelve


def shelve_add(key, content):  # 添加
    with shelve.open('data/data') as she:
        if key in she.keys() and she[key]:
            s = she[key]
            s.append(content)
            she[key] = s
        else:
            s = [content]
            she[key] = s


def shelve_open(key):  # 打开读取
    with shelve.open('data/data') as she:
        if key in she.keys() and she[key]:
            res = she[key]
            return res
        else:
            return []


def shelve_save(key, content):  # 保存
    with shelve.open('data/data') as she:
        she[key] = content


if __name__ == '__main__':
    print(shelve_open('city_done_link'))
