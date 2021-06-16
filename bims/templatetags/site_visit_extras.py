from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def can_validate_site_visit(context):
    return context['request'].user.has_perm('bims.can_validate_site_visit')
