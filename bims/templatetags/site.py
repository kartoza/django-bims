# -*- coding: utf-8 -*-
from django.contrib.flatpages.models import FlatPage
from preferences import preferences
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
import subprocess

from bims.cache import get_cache, set_cache
from bims.utils.domain import get_current_domain

register = template.Library()


@register.simple_tag
def current_domain():
    return 'http://%s' % get_current_domain()

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


@register.filter(name='remove_media_path')
def remove_media_path(value):
    return value.replace(settings.MEDIA_ROOT, '')


@register.filter
def filename(value):
    file_name = value.split('/')
    return file_name[len(file_name) - 1]


@register.simple_tag
def current_version():
    repo_path = preferences.SiteSetting.github_repo_path

    if not repo_path:
        return '-'

    # Configure Git to consider the directory safe
    try:
        subprocess.check_call(['git', 'config', '--global', '--add', 'safe.directory', repo_path])
    except subprocess.CalledProcessError as e:
        return f"Error setting safe directory: {e}"

    try:
        commit = subprocess.check_output(
            ['git', '-C', repo_path, 'log', '-n', '1', '--pretty=tformat:%H']
        ).strip().decode()
    except Exception as e:  # noqa
        return '-'

    # version = tag.name if tag else ''
    version = ''
    if not version:
        try:
            version_text = (
                subprocess.check_output(
                    ['git', '-C', repo_path, 'log', '-n', '1', '--pretty=tformat:%h-%ad', '--date=short']
                ).strip().decode()
            )
        except BrokenPipeError:
            version = '-'
            version_text = '-'

        version = (
            '<a target="_blank" '
            'href="https://github.com/kartoza/django-bims/commit/{commit}">'
            '{version_text}</a>'.format(
                commit=commit,
                version_text=version_text
            )
        )
    return mark_safe(version)


@register.filter
def space_separated(value):
    return f"{value:,}".replace(',', ' ')


@register.simple_tag
def is_debug():
    return settings.DEBUG


@register.simple_tag
def is_fada_site():
    project_name = get_cache('project_name', '')
    if not project_name:
        project_name = preferences.SiteSetting.project_name
    set_cache('project_name', project_name)
    if project_name:
        return project_name.lower() == 'fada'
    return False

@register.filter
def get_attr(obj, attr_name):
    try:
        return getattr(obj, attr_name)
    except AttributeError:
        return ''


@register.simple_tag
def get_navbar_flatpages():
    return FlatPage.objects.filter(
        extension__show_in_navbar=True).order_by('extension__display_order')


@register.simple_tag
def is_user_expert(user, experts):
    return any(expert['username'] == user.username for expert in experts)
