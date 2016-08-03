#Alerts
##介绍
- 基于Django 1.9.1， Python 2.7
- 支持所有监控平台，只需将告警信息按照要求发送到本平台即可
- 告警收敛是基于主机维度进行收敛的
- 所有告警级别都会汇总，且告警级别为Disaster的，会立即发出
- 依赖mongoDB存储数据

##安装/使用
**步骤 1**: 下载代码

```
git clone https://git.oschina.net/XJGZ/Alerts.git Alerts
```

**步骤 2**: 配置

```
cd Alerts
#修改./Alerts/views.py的第11行，将mongoDB的连接信息配置上去
#修改./Alerts/views.py的第41和86行，将校验码（密码）修改为自己定义的密码
```

**步骤 3**: 运行

```
./manage.py runserver 0.0.0.0 8000
#正式环境请使用其他的多进程/线程方式运行，如gunicorn
```

**步骤 3**: 使用

- 收集告警

```
任何告警通过以下格式，使用"Content-Type": "application/x-www-form-urlencoded"post以下字符串（需要转换成url编码）到这个接口
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
```

- 分析告警

```
使用"Content-Type": "application/x-www-form-urlencoded"post以下字符串到这个接口
ACK=xjACK
```

##告警示例

```
2016.08.03 00:40:01 至 2016.08.03 00:50:01 告警汇报 

告警对象: 192.168.1.1
汇总: 故障 2 , 恢复 1 , 剩余 1 
剩余内容: 5分钟内接口/abc/test耗时大于5秒次数:111

告警对象: 192.168.1.2
汇总: 故障 14 , 恢复 10 , 剩余 4 
剩余内容: icmppingloss qq 192.168.2.1:65
icmppingloss baidu 192.168.3.1:60

告警对象: 192.168.1.3 
汇总: 故障 2 , 恢复 0 , 剩余 2 
剩余内容: http5分钟内408次数:123
http5分钟内400次数:74
```
