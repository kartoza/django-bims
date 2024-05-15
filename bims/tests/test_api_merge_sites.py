import json
import logging
from datetime import datetime

import factory
from django.db.models import signals
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework import status

from bims.models.water_temperature import WaterTemperature
from sass.tests.model_factories import (
    SiteVisit,
    SiteVisitF
)
from bims.tests.model_factories import (
    LocationSiteF,
    LocationSite,
    BiologicalCollectionRecordF,
    BiologicalCollectionRecord,
    ChemicalRecord,
    ChemicalRecordF,
    SiteImageF,
    UserF,
    SiteImage,
    WaterTemperatureF
)
from bims.api_views.merge_sites import MergeSites


logger = logging.getLogger('bims')
PRIMARY_SITE = 'primary_site'
MERGED_SITES = 'merged_sites'


class TestApiMergeSites(FastTenantTestCase):
    def setUp(self):
        self.location_site = LocationSiteF.create()

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_merge_sites(self):
        client = TenantClient(self.tenant)
        api_url = '/api/merge-sites/'

        # Cannot merge sites without log in as superuser
        res = client.put(api_url, {})
        self.assertTrue(
            res.status_code == status.HTTP_401_UNAUTHORIZED
        )

        user = UserF.create(is_superuser=True)
        client.login(
            username=user.username,
            password='password'
        )

        secondary_site_1 = LocationSiteF.create()
        secondary_site_2 = LocationSiteF.create()

        BiologicalCollectionRecordF.create(
            site=self.location_site
        )
        BiologicalCollectionRecordF.create(
            site=secondary_site_1
        )
        BiologicalCollectionRecordF.create(
            site=secondary_site_2
        )
        ChemicalRecordF.create(
            location_site=secondary_site_1
        )
        ChemicalRecordF.create(
            location_site=secondary_site_2
        )
        SiteImageF.create(
            site=secondary_site_1
        )
        SiteImageF.create(
            site=secondary_site_2
        )
        SiteVisitF.create(
            location_site=secondary_site_1
        )
        SiteVisitF.create(
            location_site=secondary_site_2
        )
        # Cannot merge sites without providing the site ids
        res = client.put(api_url, {}, content_type='application/json')
        self.assertEqual(
            res.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        # Cannot find primary site based on the id
        res = client.put(api_url, {
            PRIMARY_SITE: '99',
            MERGED_SITES: '2,2'
        }, content_type='application/json')
        self.assertTrue(
            res.status_code == status.HTTP_400_BAD_REQUEST
        )

        res = client.put(api_url, {
            PRIMARY_SITE: str(self.location_site.id),
            MERGED_SITES: f'{str(secondary_site_1.id)},'
                          f'{str(secondary_site_2.id)}'
        }, content_type='application/json')
        self.assertTrue(
            res.status_code == status.HTTP_200_OK
        )
        self.assertEqual(
            BiologicalCollectionRecord.objects.filter(
                site=self.location_site
            ).count(), 3
        )
        self.assertEqual(
            ChemicalRecord.objects.filter(
                location_site=self.location_site
            ).count(), 2
        )
        self.assertEqual(
            SiteImage.objects.filter(
                site=self.location_site
            ).count(), 2
        )
        self.assertEqual(
            SiteVisit.objects.filter(
                location_site=self.location_site
            ).count(), 2
        )

    def test_update_sites(self):
        secondary_site_1 = LocationSiteF.create()
        secondary_site_2 = LocationSiteF.create()
        BiologicalCollectionRecordF.create(
            site=self.location_site
        )
        BiologicalCollectionRecordF.create(
            site=secondary_site_1
        )
        BiologicalCollectionRecordF.create(
            site=secondary_site_2
        )
        wt = WaterTemperatureF.create(
            date_time=datetime.strptime('10/10/24', '%m/%d/%y'),
            is_daily=True,
            value=12,
            maximum=10,
            minimum=11,
            location_site=secondary_site_1
        )
        total_records_updated = MergeSites.update_sites(
            self.location_site,
            list(LocationSite.objects.filter(
                id__in=[secondary_site_1.id, secondary_site_2.id]
            ))
        )
        wt = WaterTemperature.objects.get(id=wt.id)
        self.assertEqual(
            wt.location_site.id,
            self.location_site.id
        )
        self.assertEqual(
            total_records_updated[
                'bims.BiologicalCollectionRecord'
            ],
            2
        )
