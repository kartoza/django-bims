# From https://stackoverflow.com/a/4699069
# Convert a Python list into a JavaScript object
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.template import Library

import json

register = Library()


@register.filter(is_safe=True)
def jsonify(object):
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return json.dumps(object)


@register.simple_tag
def get_html_for_radio_group(name, sass_rating):
    column_width= 100 / 6
    try:
        value = int(sass_rating[-1])
    except:
        value = 0
    result_html = (
                '<div class="form-control sass-radio-label" '
                'name="{name}">').format(name = name)
    for x in range(0, 6):
        if x == value:
            checked = 'checked'
        else:
            checked = ''
        next_radio_button = (
            '<input type="radio" '
            'name="{name}" value="{x}" '
            '{checked}>').format(
                name=name,
                checked=checked,
                x = x)

        result_html += (
            '<span class="col-m" style="width: {column_width}%">'
            '{next_radio_button}'
            '</span>').format(
                next_radio_button=next_radio_button,
                column_width=column_width)
    result_html += '</div>'
    return result_html


@register.simple_tag
def get_html_for_radio_group_headings(column_count):
    result_html = ''
    column_width = 100 / column_count
    for x in range(0, column_count):
        result_html += (
            '<span class="col-m" style="width: {column_width}%">'
                '{x}'
            '</span>').format(x=x, column_width=column_width)
    return result_html
