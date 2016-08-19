# coding:utf-8
import time

from django.http import HttpResponse
from dwebsocket import require_websocket

# 告警平台websocket客户端对象列表
AlertClients = {}


@require_websocket
def Alerts(request):
    # websocket接口
    global AlertClients
    username = str(request.user)
    ws = request.websocket
    AlertClients.update({username: ws})
    while 1:
        if AlertClients[username] == ws:
            # socket是否断开后清除对象
            if not CheckWebSocket(username, AlertClients):
                del AlertClients[username]
                break
            time.sleep(30)
        else:
            break
    return HttpResponse(status = 204)


def CheckWebSocket(username, wsClients):
    # 检查socket是否断开，断开则返回False
    try:
        # 没消息则返回True，有消息则为消息内容，socket断开则报异常
        data = wsClients[username].read(True)
        # 收到客户端ping则回应服务端ping
        if data == 'Cping':
            wsClients[username].send('Sping')
        elif not data or data == 'close':
            return False
        return True
    except:
        return False


def sendWebSocket(username, data, wsClients):
    # 通过websocket发送消息到指定用户，username为all时，推送所有在线用户
    # data必须是utf-8编码
    if username == 'all':
        # 标记push是否有失败的情况，True则返回失败
        pushError = False
        for username in wsClients:
            ws = wsClients[username]
            if CheckWebSocket(username, wsClients):
                ws.send(data)
            else:
                # websocket是否异常，若异常，则状态标记置为True
                pushError = True
        if pushError:
            return False
        else:
            return True
    else:
        ws = wsClients.get(username)
        if ws:
            if CheckWebSocket(username, wsClients):
                ws.send(data)
                return True
            else:
                return False
        else:
            return False
