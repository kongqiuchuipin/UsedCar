# _*_ coding:utf-8 _*_
import shelve


def shelve_update(key, content):  # 添加链接集合
    with shelve.open('data/city') as she:
        if key in she.keys() and she[key]:
            s = she[key]
            bef = len(s)
            s.update(content)
            aft = len(s)
            print(key, '更新了{}条, 现有{}条'.format(aft - bef, aft))
            she[key] = s
        else:
            she[key] = content


def shelve_add(key, content):  # 添加单个对象
    with shelve.open('data/city') as she:
        if key in she.keys() and she[key]:
            s = she[key]
            s.append(content)
            she[key] = s
        else:
            s = [content]
            she[key] = s


def shelve_open(key):
    with shelve.open('data/city') as she:
        if key in she.keys() and she[key]:
            s = she[key]
        else:
            s = set()
        return s


if __name__ == '__main__':
    print(shelve_open('repeat_link'))
