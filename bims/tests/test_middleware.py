import os
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect

from preferences import preferences

from bims.middleware import RedirectHomePageMiddleware
from bims.models import SiteSetting



class RedirectHomePageMiddlewareTest(TestCase):
    def setUp(self):
        site_setting = SiteSetting.objects.get(
            id=preferences.SiteSetting.id
        )
        site_setting.homepage_redirect_url = 'https://target-page.com'
        site_setting.save()

        # Create a RequestFactory instance
        self.factory = RequestFactory()

        # Create a simple response for the get_response callable
        self.get_response = lambda request: HttpResponse("OK")

        # Create an instance of the middleware
        self.middleware = RedirectHomePageMiddleware(self.get_response)

    def test_redirect_homepage(self):
        # Create a request for the homepage
        request = self.factory.get('/')

        # Process the request through the middleware
        response = self.middleware(request)

        # Check that the response is a redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://target-page.com')

    def test_no_redirect_on_other_paths(self):
        # Create a request for a non-homepage URL
        request = self.factory.get('/other-path/')

        # Process the request through the middleware
        response = self.middleware(request)

        # Check that the response is not a redirect
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
