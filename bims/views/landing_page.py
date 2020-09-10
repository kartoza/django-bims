# coding=utf-8
from django.template.response import TemplateResponse
from django.contrib.sites.shortcuts import get_current_site

from wagtail.core.models import Site
from wagtail.core.views import serve
from bims_theme.models.theme import CustomTheme


def landing_page_view(request, *args, **kwargs):
    request_uri = request.get_host().split(':')
    request_host = request_uri[0]
    request_port = 80
    current_site = get_current_site(request)
    if len(request_uri) > 1:
        request_port = request_uri[1]
    wagtail_site = Site.objects.filter(
        hostname=request_host,
        port=request_port
    )
    if wagtail_site.exists() and request.get_host() != current_site.domain:
        return serve(request, '/')

    context = {}
    custom_theme = CustomTheme.objects.filter(is_enabled=True)
    if custom_theme.exists():
        custom_theme = custom_theme[0]
        carousel_headers = custom_theme.carousels.all()
        context['headers'] = []
        context['summaries'] = []
        for header in carousel_headers:
            context['headers'].append({
                'file': header.banner,
                'title': header.title,
                'paragraph': header.description,
                'id': header.id,
                'color': header.text_color,
                'overlay': header.background_color_overlay,
                'overlay_opacity': header.background_overlay_opacity / 100
            })
    return TemplateResponse(
        request,
        'landing_page.html',
        context
    )
