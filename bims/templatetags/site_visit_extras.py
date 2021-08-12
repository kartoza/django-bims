from django import template
from django.urls import reverse_lazy


register = template.Library()


def get_unvalidated_site_visits_url(user):
    return (
        '{base_url}?validated=["non validated"]&o=date'.
            format(
            base_url=reverse_lazy('site-visit-list'),
            id=user.id
        )
    )


@register.simple_tag(takes_context=True)
def can_validate_site_visit(context):
    return context['request'].user.has_perm('bims.can_validate_site_visit')


@register.simple_tag(takes_context=True)
def unvalidated_site_visits_url(context):
    return get_unvalidated_site_visits_url(context['request'].user)
