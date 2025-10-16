# app/templatetags/editor_fonts.py
from django import template
from django.utils.safestring import mark_safe
from bims_theme.models.font import CustomFont

register = template.Library()

@register.simple_tag
def custom_fonts_links():
    urls = CustomFont.objects.filter(is_active=True).values_list("css_url", flat=True)
    # preconnect is optional, but can help
    tags = [
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
    ]
    tags += [f'<link rel="stylesheet" href="{u}">' for u in urls if u]
    return mark_safe("\n".join(tags))
