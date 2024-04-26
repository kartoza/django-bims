# coding=utf-8
"""Tests for models."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.tests.model_factories import ProfileF, UserF


class TestProfile(FastTenantTestCase):
    """ Tests CURD Profile.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        self.client = TenantClient(self.tenant)

    def test_profile_create(self):
        """
        Tests profile creation
        """
        user = UserF.create()
        profile = ProfileF.create(user=user)

        # check if pk exists
        self.assertTrue(profile.user is not None)

        # check if qualifications and other exists
        self.assertTrue(profile.qualifications is not None)
        self.assertTrue(profile.other is not None)

    def test_profile_read(self):
        """
        Tests profile creation
        """
        user = UserF.create()
        profile = ProfileF.create(
            user=user,
            qualifications='qualifications',
            other='other'
        )
        profile.save()

        self.assertTrue(profile.qualifications == 'qualifications')
        self.assertTrue(
            profile.other == 'other')

    def test_profile_update(self):
        """
        Tests profile creation
        """
        user = UserF.create()
        profile = ProfileF.create(
            user=user
        )
        profile_data = {
            'qualifications': 'qualifications',
            'other': 'other'
        }
        profile.__dict__.update(profile_data)
        profile.save()

        # check if updated
        for key, val in profile_data.items():
            self.assertEqual(getattr(profile, key), val)

    def test_profile_delete(self):
        """
        Tests fish collection record model delete
        """
        user = UserF.create()
        profile = ProfileF.create(
            user=user
        )
        profile.delete()

        # check if deleted
        self.assertTrue(profile.pk is None)

    def test_profile_update_request(self):
        """
        Test update profile from the form page
        """
        user = get_user_model().objects.create(
            is_staff=False,
            is_active=True,
            is_superuser=False,
            username='test')
        user.set_password('psst')
        user.save()
        resp = self.client.login(
            username='test',
            password='psst'
        )
        self.assertTrue(resp)

        post_dict = {
            'first-name': 'First',
            'last-name': 'Last',
            'organization': 'Org',
            'role': 'Role'
        }

        response = self.client.post(
            '/profile/{}/'.format(user.username),
            post_dict
        )
        self.assertEqual(response.status_code, 302)
        updated_user = get_user_model().objects.get(id=user.id)
        self.assertEqual(updated_user.first_name, post_dict['first-name'])
        self.assertEqual(updated_user.bims_profile.role, post_dict['role'])
