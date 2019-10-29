import json
from mock import patch

from django.test import TestCase
from django.contrib.staticfiles.storage import staticfiles_storage
from django.shortcuts import reverse

from bims.tests.model_factories import (
    LocationSiteF,
    LocationTypeF,
    UserF
)
from bims.models import LocationSite, LocationContext


class TestLocationSiteFormView(TestCase):
    """
    Tests location site form.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        post_data_path = staticfiles_storage.path(
            'data/site_form_post_data.json')
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
        with patch('bims.tasks.location_site.'
                   'update_location_context.delay') as mock_task:
            self.client.post(
                '/location-site-form/add/',
                self.post_data,
                follow=True
            )
            self.assertTrue(mock_task.called)
        location_sites = LocationSite.objects.filter(
            site_code=self.post_data['site_code']
        )
        self.assertTrue(location_sites.exists())

    def test_LocationSiteFormUpdateView_allow_edit(self):
        user = UserF.create(id=1)
        self.client.login(
            username=user.username,
            password='password'
        )
        location_site = LocationSiteF.create(
            creator=user,
        )
        post_data = self.post_data
        post_data['id'] = location_site.id
        post_request = self.client.post(
            '/location-site-form/update/?id={}'.format(location_site.id),
            post_data,
            follow=True
        )
        # Test if user is not the creator
        location_site_2 = LocationSiteF.create()
        post_data['id'] = location_site_2.id
        post_request_2 = self.client.post(
            '/location-site-form/update/?id={}'.format(location_site_2.id),
            self.post_data,
            follow=True
        )
        # Test if user is the owner but not the creator
        location_site_3 = LocationSiteF.create(
            owner=user,
            creator=None
        )
        post_data['id'] = location_site_3.id
        post_request_3 = self.client.post(
            '/location-site-form/update/?id={}'.format(location_site_3.id),
            self.post_data,
            follow=True
        )

        self.assertEqual(post_request.status_code, 200)
        self.assertEqual(post_request_2.status_code, 404)
        self.assertEqual(post_request_3.status_code, 200)

    def test_LocationSiteFormUpdateView_post_data(self):
        location_context_path = staticfiles_storage.path(
            'data/location_context_document.json')
        location_context_file = open(location_context_path)
        location_context_document = json.load(location_context_file)
        post_data = self.post_data
        post_data['refined_geomorphological_zone'] = ''
        loc_type = LocationTypeF(
            name='PointObservation',
            allowed_geometry='POINT'
        )

        user = UserF.create(id=1)
        self.client.login(
            username=user.username,
            password='password',
        )
        location_site = LocationSiteF.create(
            location_type=loc_type,
            creator=user,
            location_context_document=location_context_document
        )
        post_data['id'] = location_site.id

        self.client.post(
            '/location-site-form/update/?id={}'.format(location_site.id),
            post_data,
            follow=True
        )
        updated_location_site = LocationSite.objects.get(
            id=location_site.id
        )
        updated_location_context = LocationContext.objects.filter(
            site=location_site
        )
        self.assertEqual(
            updated_location_site.river.name,
            'NXAMAGELE'
        )
        self.assertTrue(
            updated_location_context.filter(
                group__key__icontains='catchment_area').exists()
        )
        self.assertTrue(
            updated_location_context.filter(
                group__key='geo_class_recoded').exists()
        )
        self.assertTrue(
            updated_location_context.value_from_key('geo_class_recoded') ==
            'Mountain headwater stream')

        # Test if there are no location context data
        location_site_2 = LocationSiteF.create(
            location_type=loc_type,
            creator=user,
        )
        post_data['id'] = location_site_2.id
        post_request_2 = self.client.post(
            '/location-site-form/update/?id={}'.format(location_site_2.id),
            post_data,
            follow=True
        )
        updated_location_context_2 = LocationContext.objects.filter(
            site=location_site_2
        )
        self.assertTrue(
            updated_location_context_2.filter(
                group__key__icontains='catchment_area').exists()
        )
        self.assertTrue(
            updated_location_context_2.value_from_key('geo_class_recoded') ==
            'Mountain headwater stream')
        self.assertTrue(
            post_request_2.redirect_chain[0][0],
            '/location-site-form/update/?id={}'.format(
                location_site_2.id
            )
        )

    def test_LocationSiteFormView_delete(self):
        loc_type = LocationTypeF(
            name='PointObservation',
            allowed_geometry='POINT'
        )
        user = UserF.create(id=1)
        location_site_2 = LocationSiteF.create(
            location_type=loc_type,
            creator=user,
        )
        self.client.login(
            username=user.username,
            password='password',
        )
        post_data = {}
        post_request_2 = self.client.post(
            '/location-site-form/delete/{}/'.format(
                location_site_2.id
            ),
            post_data,
            follow=True
        )
        self.assertFalse(
            LocationSite.objects.filter(id=location_site_2.id).exists()
        )
        self.assertEqual(
            post_request_2.redirect_chain[0][0],
            reverse('location-site-form')
        )
        location_site_3 = LocationSiteF.create(
            location_type=loc_type,
        )
        post_request_3 = self.client.post(
            '/location-site-form/delete/{}/'.format(
                location_site_3.id
            ),
            post_data,
            follow=True
        )
        self.assertTrue(
            LocationSite.objects.filter(id=location_site_3.id).exists()
        )
        self.assertTrue(
            '/account/login' in post_request_3.redirect_chain[0][0],
        )
