# coding=utf-8
from django.contrib.auth.models import User
from django.template.defaultfilters import stringfilter
from easyaudit.models import CRUDEvent
from django import template

register = template.Library()


@register.filter
@stringfilter
def contribution_date(value):
    user = User.objects.get(username=value)
    date = CRUDEvent.objects.filter(user=user).latest('datetime').datetime
    return date


@register.filter
@stringfilter
def summary_contribution(value):
    user = User.objects.get(username=value)
    action = CRUDEvent.objects.filter(user=user).latest('datetime')
    event = action.get_event_type_display()
    content = action.content_type
    return '{} {}'.format(event, content)
