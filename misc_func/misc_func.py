# coding:utf-8
import smtplib
from email.mime.multipart import MIMEMultipart
import httplib
import json
#用于写html格式的邮件
from email.mime.text import MIMEText

def pushMail(subject, text, to='1018883015@qq.com'):
    # 发送邮件，最好能换成自己的展示途径
    host = '192.168.1.1'
    FROM = 'demo<1018883015@qq.com>'
    # 采用related定义内嵌资源的邮件体
    msg = MIMEMultipart('related')
    msgtext = MIMEText('''
    <style></style>
    <div><span></span>
        <div style="font-family: 微软雅黑, Tahoma; line-height: normal;"><br></div>
        <div style="line-height: normal;"><b><span style="line-height: 1.5;"><span style="font-family: 微软雅黑, Tahoma; font-size: 27px;">%s</span></div>
    </div>
    <div><br></div><hr style="width: 210px; height: 1px;" color="#b5c4df" size="1" align="left">
    <div><span><div style="MARGIN: 10px; FONT-FAMILY: verdana; FONT-SIZE: 10pt"><div>1018883015@qq.com</div></div></span></div>
    <!--<![endif]-->''' % text, 'html', 'utf-8')

    msg.attach(msgtext)
    msg['Subject'] = subject
    msg['From'] = FROM
    msg['To'] = to

    try:
        server = smtplib.SMTP()
        server.connect(host,'25')
        server.sendmail(FROM, to, msg.as_string())
        server.quit()
    except:
        if server:
            server.quit()


def httpRequest(method, url, data = '', headers = {}):
    # 封装HTTP请求
    _urlC = httplib.urlsplit(url)
    IP = _urlC.netloc.split(':')[0]
    if len(_urlC.netloc.split(':')) > 1:
        PORT = _urlC.netloc.split(':')[1]
    elif _urlC.scheme == 'https':
        PORT = 443
    else:
        PORT = 80
    try:
        if _urlC.scheme == 'https':
            httpclient = httplib.HTTPSConnection(IP, PORT, timeout = 5)
        else:
            httpclient = httplib.HTTPConnection(IP, PORT, timeout = 5)
        if _urlC.query:
            httpclient.request(method, '%s?%s' % (_urlC.path, _urlC.query), data, headers)
        else:
            httpclient.request(method, _urlC.path, data, headers)
        return httpclient.getresponse()
    except:
        return False


def PushWX(corpsecret, agentid, text, request):
    # 推送消息到企业微信
    body = 'corpsecret=%s' % corpsecret
    accesstoken = json.loads(
        httpRequest('POST', '%s://%s/api/GetWXtoken' % (request._get_scheme(), request.get_host()), body,
                    {"Content-Type": "application/x-www-form-urlencoded"}).read())['accesstoken']
    count = 0
    # 微信限制推送长度为2048，实测最大为2046，为避免出现极限情况，这里设置2000分段发送
    for i in xrange(1, len(text) / 2000 + 2):
        body = json.dumps(
            {"touser": "@all", "toparty": "@all", "msgtype": "text", "agentid": agentid, "text": {"content": text[
                                                                                                             count * 2000:i * 2000]}})
        count = i
        info = json.loads(httpRequest('POST', 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s' % accesstoken, body).read())
        # if info['errcode'] != 0:
            # I_logger.error('agentid: %s, errmsg:%s' % (agentid, info['errmsg']))


def error_res():
    # 错误请求返回结果
    return {"msg": "访问错误"}

