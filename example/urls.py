# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '06/06/18'

from django.conf.urls import url
from example.views.test_captcha import CaptchaTestView

urlpatterns = [
    url(r'^example/captcha/', CaptchaTestView.as_view())
]
