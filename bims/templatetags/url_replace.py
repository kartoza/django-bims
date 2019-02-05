from django import template
"""
Taken from https://medium.com/@sumitlni/paginate-properly-please-93e7ca776432
"""

register = template.Library()


@register.simple_tag
def url_replace(request, field, value):
    query_string = request.GET.copy()
    query_string[field] = value

    return query_string.urlencode()
