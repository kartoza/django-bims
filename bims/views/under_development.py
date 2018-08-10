# coding=utf-8
from django.views.generic import TemplateView


class UnderDevelopmentView(TemplateView):
    template_name = 'under_development.html'
