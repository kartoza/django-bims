from django.core.cache import cache
from bims_theme.models.theme import THEME_CACHE_KEY, CustomTheme


def bims_custom_theme(request):
    theme = cache.get(THEME_CACHE_KEY)
    if theme is None:
        try:
            theme = CustomTheme.objects.get(is_enabled=True)
        except Exception:  # noqa
            theme = {}
        cache.set(THEME_CACHE_KEY, theme)
    return {'custom_theme': theme}
