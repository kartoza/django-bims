# -*- coding: utf-8 -*-
from django import template
from django.contrib.sites.models import Site

register = template.Library()


@register.simple_tag
def current_domain():
    return 'http://%s' % Site.objects.get_current().domain
