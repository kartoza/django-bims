# -*- coding: utf-8 -*-
from django import template
from django.contrib.sites.models import Site

register = template.Library()


@register.simple_tag
def current_domain():
    return 'http://%s' % Site.objects.get_current().domain

# USAGE:
# {% load file_the_templatetag_is_in %}
# {{ my_hex_color| hex_to_rgb }}
# {{ my_hex_color| hex_to_rgb:'rgba({r},{g},{b}, 0.5)' }}
# {{ my_hex_color| hex_to_rgb:'Components: r:{r},g:{g},b:{b}' }}


# adapted from https://github.com/guillaumeesquevin/django-colors
@register.filter(name='hex_to_rgb')
def hex_to_rgb(hex_string, format_string='{r},{g},{b}'):
    """Returns the RGB value of a hexadecimal color"""
    hex_string = hex_string.replace('#', '')
    out = {
        'r': int(hex_string[0:2], 16),
        'g': int(hex_string[2:4], 16),
        'b': int(hex_string[4:6], 16)}
    return format_string.format(**out)
