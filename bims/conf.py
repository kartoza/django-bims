from django.conf import settings as django_settings


class LazySettings(object):
    @property
    def GRUNT_MODULES(self):
        return getattr(django_settings, "GRUNT_MODULES", {})

    @property
    def REQUIRED_JS_PATH(self):
        return getattr(django_settings, "REQUIRE_JS_PATH", {})


settings = LazySettings()


TRACK_AJAX_REQUESTS = getattr(
        django_settings,
        'TRACK_AJAX_REQUESTS',
        False)

TRACK_ANONYMOUS_USERS = getattr(
        django_settings,
        'TRACK_ANONYMOUS_USERS',
        True)

TRACK_PAGEVIEWS = getattr(
        django_settings,
        'TRACK_PAGEVIEWS',
        False)

TRACK_IGNORE_URLS = getattr(
        django_settings,
        'TRACK_IGNORE_URLS',
        (r'^(favicon\.ico|'
         r'robots\.txt|'
         r'admin[/].*|'
         r'bims_proxy[/].*|'
         r'api[/].*|tracking[/].*|'
         r'.*\.\w{2,3}|jsi18n[/].*)$',)
)

TRACK_IGNORE_USER_AGENTS = getattr(
        django_settings,
        'TRACK_IGNORE_USER_AGENTS', tuple())

TRACK_IGNORE_STATUS_CODES = getattr(
        django_settings,
        'TRACK_IGNORE_STATUS_CODES',
        [])

TRACK_REFERER = getattr(django_settings, 'TRACK_REFERER', False)

TRACK_QUERY_STRING = getattr(
        django_settings,
        'TRACK_QUERY_STRING',
        False)

# ---------------------------------------------------------------------------
# FIPS site-code generator – spatial layer configuration
# These mirror the Django settings of the same name (see project.py) so that
# application code can import them from bims.conf rather than reaching into
# django.conf.settings directly.
# ---------------------------------------------------------------------------

FIPS_GBIF_CONTINENT_LAYER = getattr(
    django_settings, 'FIPS_GBIF_CONTINENT_LAYER', 'continent')
FIPS_GBIF_CONTINENT_FIELD = getattr(
    django_settings, 'FIPS_GBIF_CONTINENT_FIELD', 'cont_code')

FIPS_BASIN_LAYER = getattr(
    django_settings, 'FIPS_BASIN_LAYER', 'basin')
FIPS_BASIN_FIELD = getattr(
    django_settings, 'FIPS_BASIN_FIELD', 'WMOBB_NAME')

FIPS_SUBBASIN_LAYER = getattr(
    django_settings, 'FIPS_SUBBASIN_LAYER', '')
FIPS_SUBBASIN_FIELD = getattr(
    django_settings, 'FIPS_SUBBASIN_FIELD', 'name')

FIPS_HYDROBASIN_LAYER = getattr(
    django_settings, 'FIPS_HYDROBASIN_LAYER', '')
FIPS_HYDROBASIN_FIELD = getattr(
    django_settings, 'FIPS_HYDROBASIN_FIELD', 'HYBAS_ID')
