import os
from django.core.exceptions import ImproperlyConfigured


def get_key(key_name):
    """
    Get key from secret.py or environment variable.
    Return empty string if key can't be found.
    """
    if key_name == 'GEOCONTEXT_URL':
        from preferences import preferences
        return preferences.GeocontextSetting.geocontext_url
    try:
        from core.settings import secret
    except ImportError:
        return ''

    try:
        from django.conf import settings
        key = getattr(settings, key_name)
    except (AttributeError, ImproperlyConfigured):
        try:
            key = getattr(secret, key_name)
        except AttributeError:
            try:
                key = os.environ[key_name]
            except KeyError:
                key = ''

    return key
