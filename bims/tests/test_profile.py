# coding=utf-8
"""Tests for models."""

from django.test import TestCase
from bims.tests.model_factories import ProfileF, UserF


class TestProfile(TestCase):
    """ Tests CURD Profile.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        pass

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
