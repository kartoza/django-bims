# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '06/06/18'

from django.urls import re_path
from example.views.test_captcha import CaptchaTestView

urlpatterns = [
    re_path(r'^example/captcha/', CaptchaTestView.as_view())
]
