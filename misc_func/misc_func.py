# coding:utf-8
import smtplib
from email.mime.multipart import MIMEMultipart
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
