from django import template
from django.utils.safestring import mark_safe


register = template.Library()


def get_list_element(list_data, active_slug):
    element = '<ul>'
    for data in list_data:
        element += '<li><a href="{url}" class="{c}">{title}</a></li>'.format(
            url=data['url'],
            title=data['title'],
            c='active' if data['slug'] == active_slug else ''
        )
        if 'children' in data:
            element += get_list_element(data['children'], active_slug)
    element += '</ul>'
    return element

@register.simple_tag(name='manual_menu')
def manual_menu(menu_data, active_slug):
    element = get_list_element(menu_data, active_slug)
    return mark_safe(element)
