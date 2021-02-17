# -*- coding: utf-8 -*-
from django import template
from django.contrib.sites.models import Site
from django.conf import settings
from django.utils.safestring import mark_safe
from preferences import preferences

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


@register.filter(name='remove_media_path')
def remove_media_path(value):
    return value.replace(settings.MEDIA_ROOT, '')


@register.filter
def filename(value):
    file_name = value.split('/')
    return file_name[len(file_name) - 1]


@register.simple_tag
def current_version():
    from git import Repo

    from datetime import datetime
    try:
        repo = Repo(preferences.SiteSetting.github_repo_path)
    except Exception as e:  # noqa
        return '-'
    tag = next(
        (tag for tag in repo.tags if tag.commit == repo.head.commit), None
    )
    version = tag.name if tag else ''
    if not version:
        version = repo.head.commit.hexsha if repo.head.commit else ''
        version_text = '{commit} ({date})'.format(
            commit=version[:8],
            date=(
                datetime.fromtimestamp(
                    repo.head.commit.committed_date).strftime(
                    '%Y-%m-%d'
                ) if repo.head.commit else ''
            )
        )
        version = (
            '<a target="_blank" '
            'href="https://github.com/kartoza/django-bims/commit/{commit}">'
            '{version_text}</a>'.format(
                commit=version,
                version_text=version_text
            )
        )
    return mark_safe(version)
