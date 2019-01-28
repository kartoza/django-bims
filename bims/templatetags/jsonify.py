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
    try:
        value = int(sass_rating[-1])
    except:
        value = 1
    result_html = ('<div class="form-control sass-radio-label" '
                    'name="{name}">').format(name = name)
    for x in range(0, 5):
        if x == (value - 1):
            checked = 'checked'
        else:
            checked = ''
        if x == 0:
            starting_space = ''
        else:
            starting_space = '&nbsp;&nbsp;&nbsp;'
        result_html += ('{starting_space}{x}&nbsp;<input type="radio" '
                        'name="{name}" value="{x}" '
                        '{checked}>').format(
                                        name=name,
                                        checked=checked,
                                        x=x+1,
                                        starting_space=starting_space)
    result_html += '</div>'
    return result_html
