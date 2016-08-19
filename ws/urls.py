#coding:utf-8
from django.conf.urls import url
from ws.views import *


urlpatterns = [

    url(r'^Alerts/$', Alerts),


]