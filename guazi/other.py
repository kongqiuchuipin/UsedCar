# _*_ coding:utf-8 _*_
from pymongo import MongoClient
import execjs
# import os
# import json
import automat
import re
import pickle

# import collections
# import execjs
# www = db = MongoClient()['guaZi']['www']
# db = MongoClient()['guaZi']
# collect = ['jinnan', 'hz', 'sh', 'su']
# for c in collect:
#     collection = db[c]
#     docs = collection.find()
#     for d in docs:
#         d.pop('_id')
#         d['名称'] = d['品牌']
#         d.pop('品牌')
#         www.insert_one(d)

# one = collection.find_one({'车源号':'3'})
# sh_links = set()
#
# with open('y') as f2:
#     x = list({i.strip() for i in f2.readlines()})
#     for i in x:
#         print(i, file=open('sh_links','a',encoding='utf-8'))

#     pa = re.compile('.+htm')
#     x = collection.find_one()['链接'][21:]
#     y = pa.search(x).group()
#     print(y)
#     in_database = {l['链接'][21:] for l in collection.find()}
#     sh_links -= in_database  # 减去数据库已经有的
#     print('数据库{}'.format(len(list(in_database))))
#     print('{}'.format(len(list(sh_links))))
# def re_htm(link):
#     link = link.replace('https://www.guazi.com', '')
#     pa = re.compile('.+htm')
#     res = pa.search(link).group()
#     return res
# def simple_link(link):
#     """
#     /su/9da3a7292bf4dd04x.htm 保存成类似这样的，方便删选，防止有的同一款车有不同网址
#     """
#     linked = link.replace('https://www.guazi.com', '')
#     pa = re.compile('.+htm')
#     se = pa.search(linked)
#     if se:
#         res = se.group()
#         return res
#
# dis = collection.find()
# res = []
# for l in dis:
#     res.append(simple_link(l['链接']))
# print(l['链接'])
# condition = {'_id':l['_id']}
# if len(l['链接']) < 26:
#     l['链接'] = 'https://www.guazi.com' + l['链接']
#     collection.update_one(condition,{'$set':l})
#     print(l)
# with open('xx') as f:
#     fr = f.readlines()
#     for i in set(fr):
#         if i.strip() and i.strip() not in res:
#             print(i.strip(), file=open('sh_links','a',encoding='utf-8'))

# for i in dis:
#     t = collection.count({'车源号':i})
#     if t>1:
#         collection.remove({'车源号':i}, 0)  # 0表示只删除1个
# with open('xxx',encoding='utf-8') as x:
#     for i in set(x.readlines()):
#         print(simple_link(i), file=open('sh_links','a',encoding='utf-8'))


# db = MongoClient()['guaZi']
# collection = db['su']
# count = collection.distinct('车源号')
# fo = collection.find()
# for i in fo:
#     if len(i['链接']) > len('https://www.guazi.com/sh/d15d0fe5d1f01155x.htm'):
#         i['链接'] = simple_link(i['链接'])
#         condition = {'_id': i['_id']}
#         caa = collection.update_one(condition, {'$set': i})
#         print(caa.raw_result)

# finder = collection.find({'价格': {'$regex': '万万'}})
# x = [i for i in finder]
# print(x)
# for c in count:
#     f = collection.count({'车源号': c})
#     if f > 1:
# m = [i for i in collection.find({'车源号': c})]
# collection.delete_one({'车源号': c})
# m[0].pop('_id')
# m[0].pop('链接')
# m[1].pop('链接')
# m[0].pop('表显里程')
# m[1].pop('表显里程')
# m[0].pop('新车价格')
# m[1].pop('新车价格')
# m[0].pop('价格')
# m[1].pop('价格')
# m[0].pop('看车地址')
# m[1].pop('看车地址')
# m[1].pop('_id')
# if m[1] != m[0]:
#     print(m)
# print(c)
# print(collection.count())
# print(len(count))
# for one in collection.find():
#     condition = {'_id': one['_id']}
#     one['价格'] = one['价格'].replace('¥', '') + '万'
#     up = collection.update_one(condition, {'$set': one})
#     print(one['价格'])
# dis = collection.distinct('车源号')
# print(collection.count())
# print(len(dis))
# for i in dis:
#     t = collection.count({'车源号':i})
#     if t>1:
#         collection.remove({'车源号':i}, 0)  # 0表示只删除1个

# collection = MongoClient()['guaZi']['test']
# doc = {'1':1,'2':2}
# collection.insert_one(doc)
# db = MongoClient()['guaZi']
# db.drop_collection('test')

# print(os.path.exists('sh_cache'))   # window 不行
# class A:
#     def ex(self):
#         cache_filename = 'sh_cache'
#         with open(cache_filename, encoding='utf-8') as cache_file:
#             text = cache_file.read().strip()
#             if text:
#                 print('导入缓存成功')
#                 ex = {}
#                 exec(text, {}, ex)
#                 begin_page = ex['last_page']
#                 print(begin_page)
# a = A()
# a.ex()
import shelve


# with shelve.open('data/data') as she:
#     with open('data/www_links') as f:
#         ll = {i.strip() for i in f.readlines()}
#         s = she['all_link']
#         s.update(ll)
#         she['all_link'] = s
#     print(len(she['all_link']))
# def shelve_save(key, values):
#     with shelve.open('data/ta') as she:
#         if key in she.keys() and she[key]:
#             s = she[key]
#             bef = len(s)
#             s.update(values)
#             aft = len(s)
#             she[key] = s
#             print('更新了{}, 共{}条'.format(aft - bef, aft))
#         else:
#             s = values
#             she[key] = s
#
#
with shelve.open('data/data') as she:
    print(len(she['all_link']))
# for i in range(12, 20):
#     shelve_save('xx', {i})
