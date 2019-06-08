from django.test import TestCase

from bims.tests.model_factories import (
    LocationSiteF
)
from sass.tests.model_factories import (
    SiteVisitF
)


class TestSiteVisitFormView(TestCase):

    def setUp(self):
        pass

    def test_site_visit_form_view(self):
        site = LocationSiteF.create()
        site_visit = SiteVisitF.create(
            location_site=site
        )
        response = self.client.get(
            '/sass/view/{}/'.format(site_visit.id)
        )
        return self.assertEqual(
            response.context['sass_version'],
            5
        )
