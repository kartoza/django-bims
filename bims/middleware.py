import re
import logging
import warnings

import django
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.utils.encoding import smart_str

from preferences import preferences

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

from bims.models import Visitor, Pageview
from bims.utils import get_ip_address, total_seconds
from bims.conf import (
    TRACK_AJAX_REQUESTS,
    TRACK_ANONYMOUS_USERS,
    TRACK_IGNORE_STATUS_CODES,
    TRACK_IGNORE_URLS,
    TRACK_IGNORE_USER_AGENTS,
    TRACK_PAGEVIEWS,
    TRACK_QUERY_STRING,
    TRACK_REFERER,
)

track_ignore_urls = [re.compile(x) for x in TRACK_IGNORE_URLS]
track_ignore_user_agents = [
    re.compile(x, re.IGNORECASE) for x in TRACK_IGNORE_USER_AGENTS
]

log = logging.getLogger(__file__)

if django.VERSION < (1, 10):
    def is_anonymous(user):
        return user.is_anonymous()
else:
    def is_anonymous(user):
        return user.is_anonymous


class VisitorTrackingMiddleware(MiddlewareMixin):
    @staticmethod
    def is_ajax(request):
        return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    def _should_track(self, user, request, response):
        # Session framework not installed, nothing to see here..
        if not hasattr(request, 'session'):
            msg = ('VisitorTrackingMiddleware installed without'
                   'SessionMiddleware')
            warnings.warn(msg, RuntimeWarning)
            return False

        # Do not track AJAX requests
        if self.is_ajax(request) and not TRACK_AJAX_REQUESTS:
            return False

        # Do not track if HTTP HttpResponse status_code blacklisted
        if response.status_code in TRACK_IGNORE_STATUS_CODES:
            return False

        # Do not tracking anonymous users if set
        if user is None and not TRACK_ANONYMOUS_USERS:
            return False

        # Do not track ignored urls
        path = request.path_info.lstrip('/')
        for url in track_ignore_urls:
            if url.match(path):
                return False

        # Do not track ignored user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        for user_agent_pattern in track_ignore_user_agents:
            if user_agent_pattern.match(user_agent):
                return False

        # everything says we should track this hit
        return True

    def _refresh_visitor(self, user, request, visit_time):
        # A Visitor row is unique by session_key
        session_key = request.session.session_key

        try:
            visitor = Visitor.objects.get(pk=session_key)
        except Visitor.DoesNotExist:
            # Log the ip address. Start time is managed via the field
            # `default` value
            ip_address = get_ip_address(request)
            visitor = Visitor(pk=session_key, ip_address=ip_address)

        # Update the user field if the visitor user is not set. This
        # implies authentication has occured on this request and now
        # the user is object exists. Check using `user_id` to prevent
        # a database hit.
        if user and not visitor.user_id:
            visitor.user_id = user.id

        # update some session expiration details
        visitor.expiry_age = request.session.get_expiry_age()
        visitor.expiry_time = request.session.get_expiry_date()

        # grab the latest User-Agent and store it
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        if user_agent:
            visitor.user_agent = smart_str(
                user_agent, encoding='latin-1', errors='ignore')

        time_on_site = 0
        if visitor.start_time:
            time_on_site = total_seconds(visit_time - visitor.start_time)
        visitor.time_on_site = int(time_on_site)

        try:
            with transaction.atomic():
                visitor.save()
        except IntegrityError:
            # there is a small chance a second response has saved this
            # Visitor already and a second save() at the same time (having
            # failed to UPDATE anything) will attempt to INSERT the same
            # session key (pk) again causing an IntegrityError
            # If this happens we'll just grab the "winner" and use that!
            visitor = Visitor.objects.get(pk=session_key)

        return visitor

    def _add_pageview(self, visitor, request, view_time):
        referer = None
        query_string = None

        if TRACK_REFERER:
            referer = request.META.get('HTTP_REFERER', None)

        if TRACK_QUERY_STRING:
            query_string = request.META.get('QUERY_STRING')

        pageview = Pageview(
            visitor=visitor, url=request.path, view_time=view_time,
            method=request.method, referer=referer,
            query_string=query_string)
        pageview.save()

    def process_response(self, request, response):
        # If dealing with a non-authenticated user, we still should track the
        # session since if authentication happens, the `session_key` carries
        # over, thus having a more accurate start time of session
        user = getattr(request, 'user', None)
        if user and is_anonymous(user):
            # set AnonymousUsers to None for simplicity
            user = None

        # make sure this is a response we want to track
        if not self._should_track(user, request, response):
            return response

        # Force a save to generate a session key if one does not exist
        if not request.session.session_key:
            request.session.save()

        return response


class RedirectHomePageMiddleware:
    """
    Middleware to redirect the homepage to a specified URL based on an environment variable.

    This middleware checks if the incoming request is for the homepage ('/') and, if so,
    redirects the request to the URL specified in the 'homepage_redirect_url' in SiteSetting.
    If homepage_redirect_url variable is not set or is empty, the middleware does nothing.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if the request is for the map page
        if request.path == '/map/':
            # Get the target URL from the environment variable
            target_url = preferences.SiteSetting.homepage_redirect_url
            if target_url:
                return redirect(target_url)

        return response
