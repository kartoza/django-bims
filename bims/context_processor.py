# coding=utf-8
"""
Our custom context processors
"""
import ast
import os
from django.conf import settings
from preferences import preferences
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


def application_name(request):
    """
    Return application name
    """
    name = get_key('APPLICATION_NAME')
    if not name:
        name = 'Django BIMS'
    return {'APPLICATION_NAME': name}


def bims_preferences(request):
    """
    For all bims preferences
    """
    return {
        'bims_preferences': settings.BIMS_PREFERENCES
    }


def google_analytic_key(request):
    """
    Return google analytic key
    """
    return {'GOOGLE_ANALYTIC_KEY': get_key('GOOGLE_ANALYTIC_KEY')}


def bing_api_key(request):
    """
    Return Bing analytic key
    """
    return {'BING_MAP_KEY': get_key('BING_MAP_KEY')}


def site_ready(request):
    """
    Return if site is ready
    """
    try:
        is_site_ready = ast.literal_eval(get_key('SITE_READY'))
    except (ValueError, SyntaxError):
        is_site_ready = True
    return {'site_ready': is_site_ready}


def download_request_purpose(request):
    from bims.models import DownloadRequestPurpose
    purpose_list = []
    for download_purpose in DownloadRequestPurpose.objects.all():
        purpose_list.append({
            'id': download_purpose.id,
            'name': download_purpose.name
        })
    return {
        'download_request_purpose': purpose_list
    }


def download_request_message(request):
    is_approval_enabled = (
        preferences.SiteSetting.enable_download_request_approval
    )
    if is_approval_enabled:
        return {
            'download_request_message': (
                'Your download request has been sent to our staff. ' +
                'This may take some time. ' +
                'You will be notified by email when your request has '
                'been accepted. ' +
                'Thank you for your patience.'
            )
        }
    return {
        'download_request_message': (
            'Your data download is underway. ' +
            'This may take some time. ' +
            'You will be notified by email when your download is ready. ' +
            'Thank you for your patience.'
        )}



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

    path_commit_file = '.commit.txt'
    commit_file = os.path.isfile(path_commit_file)
    if commit_file:
        with open(path_commit_file) as file:
            context['commit_id'] = file.readline()

    path_branch_file = '.branch.txt'
    branch_file = os.path.isfile(path_branch_file)
    if branch_file:
        with open(path_branch_file) as file:
            context['branch_name'] = file.readline()
        if context['branch_name'].strip() != 'develop':
            path_tag_file = '.tag.txt'
            tag_file = os.path.isfile(path_tag_file)
            if tag_file:
                with open(path_tag_file) as tag:
                    context['tag_version'] = tag.readline()

    return context
