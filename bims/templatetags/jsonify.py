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
