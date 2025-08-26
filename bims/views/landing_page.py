# coding=utf-8
from django.template.response import TemplateResponse
from django.contrib.sites.shortcuts import get_current_site
from preferences import preferences
from rest_framework import serializers

from bims_theme.models import CarouselHeader
from bims_theme.models.theme import CustomTheme


class HeaderSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    paragraph = serializers.CharField(source='description')
    color = serializers.CharField(source='text_color')
    overlay = serializers.CharField(source='background_color_overlay')
    overlay_opacity = serializers.SerializerMethodField()

    def get_file(self, obj: CarouselHeader):
        return getattr(obj.banner, 'name', None)

    def get_banner_url(self, obj: CarouselHeader):
        try:
            return obj.banner.url
        except Exception:
            return None

    def get_overlay_opacity(self, obj: CarouselHeader):
        val = getattr(obj, 'background_overlay_opacity', None)
        if val is None:
            return 0
        return round(float(val) / 100.0, 3)

    class Meta:
        model = CarouselHeader
        fields = [
            'id',
            'file',
            'banner_url',
            'title',
            'paragraph',
            'color',
            'overlay',
            'text_alignment',
            'text_style',
            'title_font_size',
            'description_font_size',
            'overlay_opacity',                 # 0..1 (legacy-friendly)
            'background_overlay_opacity',      # 0..100 (raw int)
            'background_color_overlay',        # explicit color
            'full_screen_background',          # legacy flag (still exposed)

            'banner_fit',                      # cover / contain / natural / stretch
            'banner_height_mode',              # auto / fixed_px / viewport_vh
            'banner_height_value',             # px or vh depending on mode
            'banner_position_x',               # left / center / right
            'banner_position_y',               # top / center / bottom

            'title_font_family',
            'title_font_weight',
            'title_letter_spacing_em',
            'title_alignment',
            'title_offset_y_percent',
            'title_line_height_pct',

            'description_font_family',
            'description_font_weight',
            'description_letter_spacing_em',
            'description_alignment',
            'description_offset_y_percent',
            'description_line_height_pct',
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
