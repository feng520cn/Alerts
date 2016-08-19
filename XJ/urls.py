"""XJ URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
import Alerts.views as Alerts
import ws.urls

urlpatterns = [

    url(r'^ws/', include(ws.urls)),

    url(r'^admin/', admin.site.urls),
    url(r'^AlertsPush$', Alerts.AlertsPush),
    url(r'^AlertsAnalysis$', Alerts.AlertsAnalysis),
    url(r'^PushWsMsg/$', Alerts.views.PushWsMsg),
    url(r'^Alerts/$', Alerts.views.Alerts),
]
