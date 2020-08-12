# coding=utf-8
from django.template.response import TemplateResponse
from wagtail.core.models import Site
from wagtail.core.views import serve
from bims.models.carousel_header import CarouselHeader


def landing_page_view(request, *args, **kwargs):
    request_uri = request.get_host().split(':')
    request_host = request_uri[0]
    request_port = 80
    if len(request_uri) > 1:
        request_port = request_uri[1]
    wagtail_site = Site.objects.filter(
        hostname=request_host,
        port=request_port
    )
    if wagtail_site.exists():
        return serve(request, '/')

    context = {}
    carousel_headers = CarouselHeader.objects.all()
    context['headers'] = []
    context['summaries'] = []
    for header in carousel_headers:
        context['headers'].append({
            'file': header.banner,
            'description': header.description,
            'id': header.id
        })
    return TemplateResponse(
        request,
        'landing_page.html',
        context
    )
