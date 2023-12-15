from django.core.cache import cache
from bims_theme.models.theme import THEME_CACHE_KEY, CustomTheme


def bims_custom_theme(request):
    request_site = None

    try:
        request_site = request.site
        cache_key = THEME_CACHE_KEY + str(request_site)
    except AttributeError:
        cache_key = THEME_CACHE_KEY

    theme = cache.get(cache_key)
    if not theme:
        try:
            theme = CustomTheme.objects.get(
                is_enabled=True,
                site=request_site
            )
        except Exception:  # noqa
            theme = {}
        cache.set(cache_key, theme)
    return {'custom_theme': theme}
