#!/usr/bin/python
# coding: utf-8
# 初始化mongodb连接池
# 关晓健 2016-07-18

import pymongo


def mongodb(host = '127.0.0.1', port = 27017, username = None, password = None, db = None):
    '''
    maxPoolSize 最大连接数
    minPoolSize 最小连接数
    maxIdleTimeMS 空闲连接回收时间
    socketTimeoutMS 网络超时时间
    connectTimeoutMS 创建连接超时时间
    '''
    if username and password and db:
        mgclient = pymongo.MongoClient('mongodb://%s:%s@%s:%s/%s' % (username, password, host, port, db), maxPoolSize = 500,
                                       minPoolSize = 5, maxIdleTimeMS = 60000, socketTimeoutMS = 10000,
                                       connectTimeoutMS = 2000)
    else:
        mgclient = pymongo.MongoClient('mongodb://%s:%s' % (host, port), maxPoolSize = 500, minPoolSize = 5,
                                       maxIdleTimeMS = 60000, socketTimeoutMS = 10000, connectTimeoutMS = 2000)
    return mgclient
