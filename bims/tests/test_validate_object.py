from django.test import TestCase
from bims.tests.model_factories import LocationSiteF


class TestValidateLocationSite(TestCase):

    def setUp(self):
        pass

    def test_validate_location_site(self):
        site = LocationSiteF.create()
        site.validated = True
        site.save()

        self.assertEqual(site.validated, True)








