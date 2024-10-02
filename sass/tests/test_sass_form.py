from dateutil.parser import parse
from django.test import TestCase
from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.models.survey import Survey
from bims.tests.model_factories import (
    UserF,
    LocationSiteF
)
from sass.tests.model_factories import (
    SiteVisitF
)


class TestSassFormView(FastTenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)

    def test_update_sass(self):
        user = UserF.create()
        self.client.login(
            username=user.username,
            password='password'
        )
        site = LocationSiteF.create()
        sass_site_visit = SiteVisitF.create(
            location_site=site,
            owner=user
        )
        date = '2022/02/02'
        response = self.client.post(
            reverse('sass-update-page', kwargs={
                'sass_id': sass_site_visit.id
            }), {
                'owner': user.id,
                'date': date
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Survey.objects.filter(
                owner=user,
                date=parse(date),
                site=site
            ).exists()
        )
