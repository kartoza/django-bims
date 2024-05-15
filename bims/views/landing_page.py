# coding=utf-8
from django.template.response import TemplateResponse
from django.contrib.sites.shortcuts import get_current_site
from preferences import preferences
from rest_framework import serializers

from bims_theme.models import CarouselHeader
from bims_theme.models.theme import CustomTheme


class HeaderSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    paragraph = serializers.CharField(source='description')
    color = serializers.CharField(source='text_color')
    overlay = serializers.CharField(source='background_color_overlay')
    overlay_opacity = serializers.SerializerMethodField()

    def get_file(self, obj: CarouselHeader):
        return obj.banner

    def get_overlay_opacity(self, obj: CarouselHeader):
        return obj.background_overlay_opacity / 100

    class Meta:
        model = CarouselHeader
        fields = [
            'file',
            'title',
            'paragraph',
            'id',
            'color',
            'overlay',
            'text_alignment',
            'text_style',
            'title_font_size',
            'description_font_size',
            'overlay_opacity'
        ]


def landing_page_view(request, *args, **kwargs):
    context = {}
    custom_theme = CustomTheme.objects.filter(
        is_enabled=True
    ).first()
    if custom_theme:
        carousel_headers = custom_theme.carousels.all()
        context['headers'] = []
        context['summaries'] = []
        context['headers'] = HeaderSerializer(
            carousel_headers, many=True
        ).data
        context['funders_partners'] = []
        if custom_theme.funders.exists():
            context['funders_partners'].append({
                'title': custom_theme.funders_section_title,
                'org': custom_theme.funders,
                'color': custom_theme.funders_section_background_color
            })
        if custom_theme.partners.exists():
            if custom_theme.partners_section_order > custom_theme.funders_section_order:
                context['funders_partners'] = [{
                    'title': custom_theme.partners_section_title,
                    'org': custom_theme.partners,
                    'color': custom_theme.partners_section_background_color
                }] + context['funders_partners']
            else:
                context['funders_partners'].append({
                    'title': custom_theme.partners_section_title,
                    'org': custom_theme.partners,
                    'color': custom_theme.partners_section_background_color
                })

    if preferences.SiteSetting.default_data_source == 'fbis':
        landing_page_template = 'landing_page_fbis.html'
    else:
        landing_page_template = 'landing_page.html'

    return TemplateResponse(
        request,
        landing_page_template,
        context
    )
