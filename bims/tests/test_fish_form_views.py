# coding=utf-8
"""Tests for models."""

from django.test import TestCase, Client
from bims.tests.model_factories import (
    LocationSiteF,
    UserF
)
from geonode.people.models import Profile


class TestFishFormView(TestCase):
    """ Tests Fish Form View.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        self.client = Client()
        self.admin_user = UserF.create(
            is_superuser=True,
            is_staff=True,
            username='test',
        )
        self.admin_user.set_password('test')
        self.admin_user.save()
        self.location_site = LocationSiteF.create()

    def test_get_fish_form(self):
        """
        Test fish form get method
        """
        # Login
        login_response = self.client.post(
            '/login/', {'username': 'test', 'password': 'test'})
        self.assertTrue(login_response, 200)

        response = self.client.get(
            '/fish-form/?siteId={}'.format(
                self.location_site.id
            )
        )
        self.assertIsNotNone(response.context)
