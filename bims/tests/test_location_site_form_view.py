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
        self.client.post(
            '/location-site-form/add/',
            self.post_data,
            follow=True
        )
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
        self.assertEqual(post_request.status_code, 200)
        self.assertEqual(post_request_2.status_code, 404)

    def test_LocationSiteFormUpdateView_post_data(self):
        location_context_path = staticfiles_storage.path(
            'data/location_context_document.json')
        location_context_file = open(location_context_path)
        location_context_document = json.load(location_context_file)
        post_data = self.post_data
        post_data['refined_geomorphological_zone'] = ''

        user = UserF.create(id=1)
        self.client.login(
            username=user.username,
            password='password'
        )
        location_site = LocationSiteF.create(
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
        self.assertTrue(True)
        self.assertEqual(
            updated_location_site.river.name,
            'NXAMAGELE'
        )
        updated_location_context = json.loads(
            updated_location_site.location_context
        )
        self.assertTrue(
            'river_ecoregion_group' in
            updated_location_context['context_group_values']
        )
        self.assertTrue(
            'geomorphological_group' in
            updated_location_context['context_group_values']
        )
        self.assertTrue(
            updated_location_context['context_group_values']
            ['geomorphological_group']
            ['service_registry_values']
            ['geo_class_recoded']
            ['value'] == 'Mountain headwater stream')

        # Test if there are no location context data
        location_site_2 = LocationSiteF.create(
            creator=user,
        )
        post_data['id'] = location_site_2.id
        post_request_2 = self.client.post(
            '/location-site-form/update/?id={}'.format(location_site_2.id),
            post_data,
            follow=True
        )
        updated_location_site_2 = LocationSite.objects.get(
            id=location_site_2.id
        )
        updated_location_context_2 = json.loads(
            updated_location_site_2.location_context
        )
        self.assertTrue(
            'river_ecoregion_group' not in
            updated_location_context_2['context_group_values']
        )
        self.assertTrue(
            updated_location_context_2['context_group_values']
            ['geomorphological_group']
            ['service_registry_values']
            ['geo_class_recoded']
            ['value'] == 'Mountain headwater stream')
        self.assertTrue(
            post_request_2.redirect_chain[0][0],
            '/location-site-form/update/?id={}'.format(
                location_site_2.id
            )
        )
