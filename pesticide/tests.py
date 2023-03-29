from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from bims.tests.model_factories import (
    LocationSiteF, LocationContextF, LocationContextGroupF
)
from bims.models import BaseMapLayer


class PesticideDashboardViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create(
            username='testuser')
        self.user.set_password('testpassword')
        self.user.save()

        # Create a LocationSite object for testing
        self.location_site = LocationSiteF.create(
            name='Test Location', site_code='TL01')

        # Create a LocationContext object for testing
        location_context_group = LocationContextGroupF.create(
            name='Pesticide Risk',
            key='mv_algae_risk',
            geocontext_group_key='pesticide_risk'
        )
        self.location_context = LocationContextF.create(
            site=self.location_site,
            group=location_context_group,
            value='Very Low'
        )

        # Create a BaseMapLayer object for testing
        BaseMapLayer.objects.create(
            title='Bing Test',
            source_type='bing',
            key='test_bing_key')

    def test_login_required(self):
        response = self.client.get(
            f'/pesticide-dashboard/{self.location_site.id}/')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_context_data(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(
            f'/pesticide-dashboard/{self.location_site.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['location_site'], self.location_site)
        self.assertEqual(response.context['bing_key'], 'test_bing_key')

        expected_pesticide_risk = (
            '{"mv_algae_risk": "Very Low"}'
        )
        self.assertEqual(
            response.context['pesticide_risk'], expected_pesticide_risk)
