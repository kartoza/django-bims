import json
from datetime import datetime
from unittest.mock import patch

import factory
from django.db.models import signals

from bims.models.location_site import LocationSite
from django.contrib.gis.geos import Point
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from bims.tests.model_factories import (
    LocationSiteF, TaxonomyF,
    TaxonGroupF, UserF, BiotopeF, SamplingMethodF, RiverF
)
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.survey import Survey
from bims.models.record_type import RecordType
from bims.models.site_setting import SiteSetting
from bims.models.abundance_type import AbundanceType


class TestLocationSiteMobile(TestCase):

    def test_get_nearest_location_sites_without_coord(self):
        api_url = (
            reverse('mobile-nearest-sites')
        )
        client = APIClient()
        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_404_NOT_FOUND
        )

    def test_get_nearest_location_sites(self):
        LocationSiteF.create(
            geometry_point=Point(
                -31,
                30
            )
        )

        api_url = (
                reverse('mobile-nearest-sites') +
                '?lat=30.001&lon=-31.001'
        )
        client = APIClient()
        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )
        self.assertTrue(len(res.data) > 0)

    def test_get_nearest_sites_by_extent(self):
        LocationSiteF.create(
            geometry_point=Point(
                23.366389,
                -32.380556
            )
        )
        api_url = (
                reverse('mobile-nearest-sites') +
                '?extent=22.554688,-32.402798,23.554688,-31.402798'
        )
        client = APIClient()
        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )
        self.assertTrue(len(res.data) > 0)


class TestAllTaxaAPI(TestCase):
    def test_get_all_taxa_without_module(self):
        api_url = (
            reverse('all-taxa')
        )
        client = APIClient()
        user = UserF.create(is_superuser=True)
        client.login(
            username=user.username,
            password='password'
        )
        res = client.get(api_url)
        self.assertEqual(
            res.status_code,
            status.HTTP_404_NOT_FOUND)

    def test_get_all_taxa(self):
        taxon = TaxonomyF.create(
            rank='SPECIES'
        )
        taxon_group = TaxonGroupF.create(
            taxonomies=(taxon,)
        )

        api_url = (
                reverse('all-taxa') +
                f'?module={taxon_group.id}'
        )
        client = APIClient()
        user = UserF.create(is_superuser=True)
        client.login(
            username=user.username,
            password='password'
        )
        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            taxon.id,
            res.data[0].get('id')
        )


class TestChoicesApi(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user = UserF.create(is_superuser=True)
        self.client.login(
            username=user.username,
            password='password'
        )
        self.api_url = reverse('all-choices')

    def test_get_all_choices_without_module(self):
        res = self.client.get(self.api_url)
        self.assertEqual(
            res.status_code, status.HTTP_404_NOT_FOUND
        )

    def test_get_all_choices(self):
        taxon_group = TaxonGroupF.create()
        biotope = BiotopeF.create(
            biotope_type='broad',
            taxon_group=(taxon_group,)
        )
        res = self.client.get(
            self.api_url + f'?module={taxon_group.id}'
        )
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            res.data.get('broad_biotope')[0]['id'],
            biotope.id
        )


class TestAddSiteVisit(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = UserF.create(is_superuser=True)
        self.client.login(
            username=self.user.username,
            password='password'
        )
        self.api_url = reverse('mobile-add-site-visit')

    def test_add_survey_without_data(self):
        res = self.client.post(
            self.api_url,
            {}
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_survey(self):
        location_site = LocationSiteF.create()
        data = {
            'date': '2022-12-30',
            'owner_id': f'{self.user.id}',
            'site-id': location_site.id
        }
        res = self.client.post(
            self.api_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Survey.objects.filter(
                date=data['date'],
                owner=self.user,
                collector_user=self.user,
                site=location_site
            ).count() == 1
        )

    def test_add_survey_occurrences(self):
        location_site = LocationSiteF.create()
        AbundanceType.objects.get_or_create(
            name='Number'
        )
        taxa = TaxonomyF.create()
        biotope = BiotopeF.create(
            biotope_type='broad'
        )
        specific_biotope = BiotopeF.create(
            biotope_type='specific'
        )
        substratum = BiotopeF.create(
            biotope_type='substratum'
        )
        sampling_method = SamplingMethodF.create()

        data = {
            'date': '2022-12-30',
            'owner_id': f'{self.user.id}',
            'site-id': location_site.id,
            'taxa-id-list': f'{taxa.id}',
            f'{taxa.id}-observed': 'True',
            f'{taxa.id}-abundance': '10',
            'abundance_type': 'number',
            'record_type': 'mobile',
            'biotope': biotope.id,
            'specific_biotope': specific_biotope.id,
            'substratum': substratum.id,
            'sampling_method': sampling_method.id
        }
        res = self.client.post(
            self.api_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(len(res.data), 1)
        bio = BiologicalCollectionRecord.objects.filter(
            survey=res.data['survey_id'],
            abundance_type__name='Number'
        ).first()
        self.assertEqual(
            bio.sampling_method, sampling_method
        )
        self.assertEqual(
            bio.biotope, biotope
        )

    def test_add_survey_occurrences_missing_abundance(self):
        location_site = LocationSiteF.create()
        taxa = TaxonomyF.create()
        taxa_2 = TaxonomyF.create()

        data = {
            'date': '2022-12-30',
            'owner_id': self.user.id,
            'site-id': location_site.id,
            'taxa-id-list': ','.join([f'{taxa.id}', f'{taxa_2.id}']),
            f'{taxa.id}-observed': 'True',
            f'{taxa.id}-abundance': '10',
            'abundance_type': 'number',
            'record_type': 'mobile',
        }
        res = self.client.post(
            self.api_url,
            data
        )
        self.assertEqual(len(res.data), 1)
        self.assertTrue(RecordType.objects.filter(
            name='mobile'
        ).exists())


class TestAddLocationSite(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = UserF.create(is_superuser=True)
        self.client.login(
            username=self.user.username,
            password='password'
        )

        self.api_url = reverse('mobile-add-location-site')
        self.post_data = {
            'owner': str(self.user.id),
            'date': int(datetime.now().timestamp()),
            'latitude': 1,
            'longitude': 1,
            'ecosystem_type': 'river',
            'river_name': 'RIVER',
            'site_code': 'SITE_CODE',
            'description': 'desc',
            'additional_data': json.dumps({
                'source_collection': 'mobile'
            })
        }

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_location_site(self):
        location_site = LocationSiteF.create(
            additional_data={
                'data': 'test'
            },
            owner=self.user
        )
        update_url = reverse('location-site-update-form')
        post_data = self.post_data
        post_data['id'] = location_site.id
        res = self.client.post(
            update_url,
            post_data
        )
        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        location_site = LocationSite.objects.get(
            id=location_site.id
        )
        self.assertEqual(
            location_site.additional_data.get('source_collection'),
            'mobile'
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_add_location_site(self):
        res = self.client.post(
            self.api_url,
            self.post_data,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        location_site = LocationSite.objects.get(
            id=res.data['id']
        )
        self.assertEqual(
            location_site.additional_data.get('source_collection'),
            'mobile'
        )
        self.assertEqual(
            location_site.ecosystem_type,
            'River'
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_add_wetland_location_site(self):
        self.post_data['ecosystem_type'] = 'wetland'
        self.post_data['wetland_name'] = 'na me'
        self.post_data['wetland_data'] = {
            'wetlid': 'TEST',
            'hgm_type': 'hydrogeomorphic',
            'quaternary': 'quaternary'
        }
        res = self.client.post(
            self.api_url,
            data=self.post_data,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        location_site = LocationSite.objects.get(
            id=res.data['id']
        )
        self.assertEqual(
            location_site.ecosystem_type,
            'Wetland'
        )
        self.assertEqual(
            location_site.hydrogeomorphic_type,
            'hydrogeomorphic'
        )
        self.assertEqual(
            location_site.wetland_id,
            'TEST'
        )
        self.assertTrue(
            '-DESC-' in location_site.site_code,
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_add_wetland_location_site_without_wetland_data(self):
        self.post_data['ecosystem_type'] = 'wetland'
        self.post_data['wetland_name'] = 'NAME'
        res = self.client.post(
            self.api_url,
            data=self.post_data,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        location_site = LocationSite.objects.get(
            id=res.data['id']
        )
        self.assertEqual(
            location_site.ecosystem_type,
            'Wetland'
        )
        self.assertEqual(
            location_site.hydrogeomorphic_type,
            ''
        )
        self.assertEqual(
            location_site.wetland_id,
            ''
        )


class TestRiverName(TestCase):
    def setUp(self):
        self.client = Client()
        self.river = RiverF.create()

    @patch('mobile.api_views.river.fetch_river_name')
    def test_fetch_river_name(self, mock_fetch_river_name):
        user = UserF.create(is_superuser=True)
        self.client.login(
            username=user.username,
            password='password'
        )
        mock_fetch_river_name.return_value = self.river.name
        response = self.client.get(
            reverse('fetch-river-name'),
            {'lat': '50', 'lon': '50'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['river_name'], self.river.name)

        mock_fetch_river_name.assert_called_once_with('50', '50')
