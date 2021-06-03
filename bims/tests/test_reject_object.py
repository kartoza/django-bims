from django.test import TestCase
from bims.tests.model_factories import LocationSiteF


class TestRejectLocationSite(TestCase):

    def setUp(self):
        pass

    def test_reject_location_site(self):
        site = LocationSiteF.create()
        site.rejected = True
        site.save()

        self.assertEqual(site.rejected, True)








