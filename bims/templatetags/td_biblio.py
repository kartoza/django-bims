# -*- coding: utf-8 -*-
from django import template

register = template.Library()


@register.filter
def publication_date(entry):
    """We expect an entry object to filter"""
    if entry.is_partial_publication_date:
        fmt = "%Y"
    else:
        fmt = "%F %Y"
    return entry.publication_date.strftime(fmt)
