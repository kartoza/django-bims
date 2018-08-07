# coding=utf-8
"""
Our custom context processors
"""
from bims.utils.get_key import get_key


# noinspection PyPep8Naming
def add_recaptcha_key(request):
    """Add recaptcha site key to the context

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


def google_analytic_key(request):
    """
    Return google analytic key
    """
    return {'GOOGLE_ANALYTIC_KEY': get_key('GOOGLE_ANALYTIC_KEY')}


def custom_navbar_url(request):
    """Add custom url for navbar."""

    from django.conf import settings

    context = {}
    try:
        context['upload_url'] = settings.NAVBAR_UPLOAD_URL
    except AttributeError:
        context['upload_url'] = None

    try:
        context['ext_resource_url'] = settings.NAVBAR_EXTERNAL_RESOURCES_URL
    except AttributeError:
        context['ext_resource_url'] = None

    try:
        context['doc_report_url'] = settings.NAVBAR_DOCUMENTS_REPORT_URL
    except AttributeError:
        context['doc_report_url'] = None

    try:
        context['contact_url'] = settings.NAVBAR_CONTACT_URL
    except AttributeError:
        context['contact_url'] = None

    try:
        context['biblio_url'] = settings.NAVBAR_BIBLIOGRAPHY_URL
    except AttributeError:
        context['biblio_url'] = None

    try:
        context['profile_url'] = settings.NAVBAR_PROFILE_URL
    except AttributeError:
        context['profile_url'] = None

    try:
        context['contributions_url'] = settings.NAVBAR_CONTRIBUTIONS_URL
    except AttributeError:
        context['contributions_url'] = None

    try:
        context['title_bims_abbr'] = settings.TITLE_BIMS_ABBREVIATION
    except AttributeError:
        context['title_bims_abbr'] = None

    try:
        context['title_bims_long'] = settings.TITLE_BIMS_LONG
    except AttributeError:
        context['title_bims_long'] = None

    return context
