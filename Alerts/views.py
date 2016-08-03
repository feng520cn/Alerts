# coding:utf-8
import time

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt  # 临时关闭csrf检查

from misc_func.misc_func import *
from init.mongodb import *

# 初始化mongodb连接池
mgclient = mongodb()


@csrf_exempt
def AlertsPush(request):
    # 接收告警信息
    '''
    使用"Content-Type": "application/x-www-form-urlencoded"post以下字符串（需要转换成url编码）到这个接口
    {"type": "0",
    "level": "告警级别",
    "item": "告警项",
    "value": "当前值",
    "hostname": "主机名",
    "datetime": "告警时间",
    "EventID": "事件id",
    "ACK": "xjACK"}

    {"type": "1",
    "level": "告警级别",
    "item": "告警项",
    "value": "当前值",
    "hostname": "主机名",
    "datetime": "恢复时间",
    "EventID": "事件id",
    "ACK": "xjACK"}
    '''
    if request.method == 'POST':
        # 校验码
        ACK = request.POST['ACK']
        # 正式环境请修改成其他ACK
        if ACK != 'xjACK':
            return HttpResponse(status = 403)

        # '0'为故障，'1'为恢复(字符串)
        type = request.POST['type']
        hostname = request.POST['hostname']
        datetime = request.POST['datetime']
        EventID = request.POST['EventID']
        level = request.POST['level']
        item = request.POST['item']
        value = request.POST['value']

        NewTime = mgclient.monitor.Time.find_one({"type": "New"}, {"_id": 0, "Time": 1})["Time"]

        if type == '0':
            # 告警信息存放在monitor库的Alerts集合下，一个告警一条记录
            # upsert为True时，不存在会插入，默认为False，$setOnInsert存在会跳过
            # "NewTime": {"hostname": hostname, "EventID": EventID, "type": type, "level": level, "item": item, "value": value, "Sdatetime": datetime}
            mgclient.monitor.Alerts.update_one({"%s.hostname" % NewTime: hostname, "%s.EventID" % NewTime: EventID},
                                               {"$setOnInsert": {"%s.type" % NewTime: '0', "%s.level" % NewTime: level, "%s.item" % NewTime: item, "%s.value" % NewTime: value, "%s.hostname" % NewTime: hostname, "%s.EventID" % NewTime: EventID}, "$set": {"%s.Sdatetime" % NewTime: datetime}},
                                               upsert = True)
            if level == 'Disaster':
                text = '告警对象: %s \n告警内容: %s:%s \n发生时间: %s' % (hostname, item, value, datetime)
                # 发出告警
                pushMail('告警', text)
        else:
            mgclient.monitor.Alerts.update_one({"%s.hostname" % NewTime: hostname, "%s.EventID" % NewTime: EventID},
                                               {"$setOnInsert": {"%s.level" % NewTime: level, "%s.item" % NewTime: item, "%s.value" % NewTime: value, "%s.hostname" % NewTime: hostname, "%s.EventID" % NewTime: EventID}, "$set": {"%s.type" % NewTime: '1', "%s.Edatetime" % NewTime: datetime}},
                                               upsert = True)
        return HttpResponse(status = 204)
    else:
        return HttpResponse(status = 404)


@csrf_exempt
def AlertsAnalysis(request):
    # 分析告警
    '''
    使用"Content-Type": "application/x-www-form-urlencoded"post以下字符串到这个接口
    ACK=xjACK
    '''
    if request.method == 'POST':
        # 校验码
        ACK = request.POST['ACK']
        # 正式环境请修改成其他ACK
        if ACK != 'xjACK':
            return HttpResponse(status = 403)

        # 更新OldTime和NewTime
        OldTime = mgclient.monitor.Time.find_one({"type": "New"}, {"_id": 0, "Time": 1})["Time"]
        mgclient.monitor.Time.update_one({"type": "Old"}, {"$set": {"Time": OldTime}})
        NewTime = str(int(time.time()))
        mgclient.monitor.Time.update_one({"type": "New"}, {"$set": {"Time": NewTime}})

        text = ''

        # 获取去重后的主机名
        for host in mgclient.monitor.Alerts.distinct("%s.hostname" % OldTime):
            # 一个主机下的所有剩余告警内容
            AllFaults = ''
            type0 = mgclient.monitor.Alerts.find({"%s.hostname" % OldTime: host, "%s.type" % OldTime: '0'},
                                                 {"_id": 0}).count()
            type1 = mgclient.monitor.Alerts.find({"%s.hostname" % OldTime: host, "%s.type" % OldTime: '1'},
                                                 {"_id": 0}).count()

            # 入库恢复告警
            for fault in mgclient.monitor.Alerts.find({"%s.hostname" % OldTime: host, "%s.type" % OldTime: '1'}):
                # {"hostname": hostname, "EventID": EventID, "type": type, "level": level, "item": item, "value": value, "Sdatetime": datetime, "Edatetime": Edatetime}
                mgclient.monitor.summary.update_one({"hostname": host, "EventID": fault[OldTime]["EventID"]},
                                                    {"$setOnInsert": {"level": fault[OldTime]["level"], "item":
                                                        fault[OldTime]["item"], "value": fault[OldTime][
                                                        "value"], "hostname": host, "EventID": fault[OldTime][
                                                        "EventID"], "Sdatetime": fault[OldTime].get(
                                                        "Sdatetime")}, "$set": {"type": fault[OldTime][
                                                        "type"], "Edatetime": fault[OldTime]["Edatetime"]}},
                                                    upsert = True)


            # 根据主机名，获取所有剩余告警内容
            for fault in mgclient.monitor.Alerts.find({"%s.hostname" % OldTime: host, "%s.type" % OldTime: '0'}):
                mgclient.monitor.summary.update_one({"hostname": host, "EventID": fault[OldTime]["EventID"]},
                                                    {"$setOnInsert": {"type": fault[OldTime]["type"], "level":
                                                        fault[OldTime]["level"], "item": fault[OldTime][
                                                        "item"], "value": fault[OldTime][
                                                        "value"], "hostname": host, "EventID": fault[OldTime][
                                                        "EventID"]}, "$set": {"Sdatetime": fault[OldTime][
                                                        "Sdatetime"]}}, upsert = True)
                AllFaults = '%s:%s\n%s' % (fault[OldTime]["item"], fault[OldTime]["value"], AllFaults)
            if AllFaults:
                text = "%s\n告警对象: %s \n汇总: 故障 %s , 恢复 %s , 剩余 %s \n剩余内容: %s" % (
                    text, host, type1 + type0, type1, type0, AllFaults)
        if text:
            text = '%s 至 %s 告警汇报 \n%s' % (time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(int(OldTime))),
                                          time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(int(NewTime))), text)
            # 发出告警
            pushMail('告警', text)

        mgclient.monitor.Alerts.remove({OldTime: {"$type": 3}})

        return HttpResponse(status = 204)
    else:
        return HttpResponse(status = 404)
