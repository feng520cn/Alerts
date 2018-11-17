# coding:utf-8
import time
import json

from django.http import HttpResponse, HttpResponseRedirect

# 临时关闭csrf检查
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth

from misc_func.misc_func import *
from init.mongodb import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import JsonResponse
from ws.views import sendWebSocket, AlertClients


# 初始化mongodb连接池
mgclient = mongodb()


def login(request):
    # 登录页
    if request.method == "POST":
        username = request.POST.get("username", None)
        password = request.POST.get("password", None)
        user_auth = auth.authenticate(username = username, password = password)
        if user_auth:
            auth.login(request, user_auth)
            return HttpResponseRedirect("/index/")
        else:
            output = '账号或密码错误，请重新输入'
    else:
        output = ''
    return render_to_response("login.html", {"auth_err": output},
                              # 解决python传变量到html时，csrf防护的问题。
                              context_instance = RequestContext(request))


def logout(request):
    # 注销页
    login_user_info = request.user
    auth.logout(request)
    return render_to_response("logout.html", {"user_info": login_user_info})


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
                PushWX('corpsecret', agentid, text, request)
                pushMail('告警', text)
        else:
            mgclient.monitor.Alerts.update_one({"%s.hostname" % NewTime: hostname, "%s.EventID" % NewTime: EventID},
                                               {"$setOnInsert": {"%s.level" % NewTime: level, "%s.item" % NewTime: item, "%s.value" % NewTime: value, "%s.hostname" % NewTime: hostname, "%s.EventID" % NewTime: EventID}, "$set": {"%s.type" % NewTime: '1', "%s.Edatetime" % NewTime: datetime}},
                                               upsert = True)
        # 推送websocket
        sendWebSocket('all', json.dumps(
            {"type": type, "level": level, "item": item, "value": value, "hostname": hostname, "datetime": datetime, "EventID": EventID}),
                      AlertClients)
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
            sendWebSocket('all', json.dumps({"OldTime": OldTime, "NewTime": NewTime, "text": text}), AlertClients)
            PushWX('corpsecret', agentid, text, request)

        mgclient.monitor.Alerts.remove({OldTime: {"$type": 3}})

        return HttpResponse(status = 204)
    else:
        return HttpResponse(status = 404)


@login_required
def PushWsMsg(request):
    # 通过websocket推送消息
    login_user_info = request.user
    if request.method == "POST":
        if login_user_info.is_superuser:
            username = request.POST["username"]
            data = request.POST["data"].encode('utf-8')
            if sendWebSocket(username, data, AlertClients):
                output = "推送成功"
            else:
                output = "部分用户推送失败"
        else:
            output = "无权限操作"
    else:
        output = ''
    return render_to_response("PushWsMsg.html", {"user_info": login_user_info, "PushMsg_info": output},
                              context_instance = RequestContext(request))


@login_required
def Alerts(request):
    # 通过websocket推送消息
    login_user_info = request.user
    if request.method == "GET":
        return render_to_response("Alerts.html", {"user_info": login_user_info},
                                  context_instance = RequestContext(request))
    return HttpResponse(status = 403)


@csrf_exempt
def GetWXtoken(request):
    # 获取微信access_token
    if request.method == 'POST':
        corpsecret = request.POST['corpsecret']
        # 企业id
        corpid = '1000002'
        # accesstoken缓存在mongodb
        try:
            accesstoken = mgclient.wx.accesstoken.find_one({"corpid": corpid, "corpsecret": corpsecret},
                                                           {"_id": 0, "accesstoken": 1})["accesstoken"]
        except:
            accesstoken = '_cuZyl2GAV1HcgzLSCvOyr-lmo-mpmycmaS3ZImH9Bc'

        errcode = json.loads(
            httpRequest('POST', 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s' % accesstoken,
                        '{"msgtype":"text"}').read())['errcode']
        # 如果accesstoken失效，则重新获取
        if errcode != 0:
            accesstoken = json.loads(httpRequest('GET',
                                                 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' % (
                                                 corpid, corpsecret)).read())['access_token']
            mgclient.wx.accesstoken.update_one({"corpid": corpid, "corpsecret": corpsecret},
                                               {"$set": {"accesstoken": accesstoken}}, upsert = True)
        return JsonResponse({"accesstoken": accesstoken})
    return JsonResponse(error_res())


