from django.core.cache import cache
from django_tenants.utils import get_tenant

from bims_theme.models.theme import THEME_CACHE_KEY, CustomTheme


def bims_custom_theme(request):
    try:
        cache_key = THEME_CACHE_KEY + get_tenant(request).name
    except AttributeError:
        cache_key = THEME_CACHE_KEY

    theme = cache.get(cache_key)
    if not theme:
        try:
            theme = CustomTheme.objects.filter(
                is_enabled=True
            ).first()
        except Exception:  # noqa
            theme = {}
        cache.set(cache_key, theme)
    return {'custom_theme': theme}
