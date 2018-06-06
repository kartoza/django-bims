# coding=utf-8
"""
Our custom context processors
"""


# noinspection PyPep8Naming
def add_recaptcha_key(request):
    """Add our Intercom.io app ID to the context

    :param request: Http Request obj

    """
    try:
        from core.settings.secret import RECAPTCHA_SITE_KEY
    except ImportError:
        RECAPTCHA_SITE_KEY = None

    if RECAPTCHA_SITE_KEY:
        return {'recaptcha_site_key': RECAPTCHA_SITE_KEY}
    else:
        return {}
