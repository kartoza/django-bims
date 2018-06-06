# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '06/06/18'

from django.views.generic import TemplateView


class CaptchaTestView(TemplateView):
    """View to test including captcha template."""
    
    template_name = 'captcha-test.html'
