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

TRACK_USING_GEOIP = getattr(
        django_settings,
        'TRACK_USING_GEOIP',
        False)
if hasattr(django_settings, 'TRACKING_USE_GEOIP'):
    raise DeprecationWarning(
            'TRACKING_USE_GEOIP is now TRACK_USING_GEOIP')

TRACK_REFERER = getattr(django_settings, 'TRACK_REFERER', False)

TRACK_QUERY_STRING = getattr(
        django_settings,
        'TRACK_QUERY_STRING',
        False)
