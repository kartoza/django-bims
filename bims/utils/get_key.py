import os
from django.conf import settings


def get_key(key_name):
    """
    Get key from secret.py or environment variable.
    Return empty string if key can't be found.
    """
    try:
        from core.settings import secret
    except ImportError:
        return ''

    try:
        key = getattr(settings, key_name)
    except AttributeError:
        try:
            key = getattr(secret, key_name)
        except AttributeError:
            try:
                key = os.environ[key_name]
            except KeyError:
                key = ''

    return key
