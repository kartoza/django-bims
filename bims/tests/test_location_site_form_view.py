import json

from django.test import TestCase
from django.contrib.staticfiles.storage import staticfiles_storage

from bims.tests.model_factories import (
    LocationSiteF,
    UserF
)
from bims.models import LocationSite


class TestLocationSiteFormView(TestCase):
    """
    Tests location site form.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        post_data_path = staticfiles_storage.path('data/site_form_post_data.json')
        post_data_file = open(post_data_path)
        self.post_data = json.load(post_data_file)

    def test_LocationSiteFormView_non_logged_in_user_access(self):
        """
        Tests open form for non logged in user
        """
        response = self.client.get(
            '/location-site-form/add/'
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_LocationSiteFormView_logged_in_user_access(self):
        """
        Tests open form for logged in user
        """
        user = UserF.create()
        self.client.login(
            username=user.username,
            password='password'
        )
        response = self.client.get(
            '/location-site-form/add/'
        )
        self.assertEqual(response.status_code, 200)

    def test_LocationSiteFormView_post_data(self):
        """
        Test post data to LocationSiteFormView
        """
        user = UserF.create(
            id=1
        )
        self.client.login(
            username=user.username,
            password='password'
        )
        post_request = self.client.post(
            '/location-site-form/add/',
            self.post_data,
            follow=True
        )
        location_sites = LocationSite.objects.filter(
            site_code=self.post_data['site_code']
        )
        self.assertTrue(location_sites.exists())
