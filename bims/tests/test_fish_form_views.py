# coding=utf-8
"""Tests for models."""

from django.test import TestCase, Client
from allauth.utils import get_user_model
from bims.tests.model_factories import (
    LocationSiteF,
)


class TestFishFormView(TestCase):
    """ Tests Fish Form View.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        self.client = Client()
        self.location_site = LocationSiteF.create()

    def test_get_fish_form(self):
        """
        Test fish form get method
        """
        # Login
        user = get_user_model().objects.create(
            is_staff=True,
            is_active=True,
            is_superuser=True,
            username='@.test')
        user.set_password('psst')
        user.save()
        resp = self.client.login(
            username='@.test',
            password='psst'
        )
        self.assertTrue(resp)

        response = self.client.get(
            '/fish-form/?siteId={}'.format(
                self.location_site.id
            )
        )
        self.assertIsNotNone(response.context)
