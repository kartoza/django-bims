# coding: utf-8
__author__ = 'Alison Mukoma <alison@kartoza.com>'
__copyright__ = 'kartoza.com'

from django.conf.urls import url
from .views.links import LinksCategoryView


urlpatterns = [
    url(r'^$', LinksCategoryView.as_view(), name='list' ),
]
