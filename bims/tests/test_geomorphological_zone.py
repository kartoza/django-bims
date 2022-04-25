from bims.tests.model_factories import LocationSiteF, LocationContextF, \
    LocationContextGroupF
from django.test import TestCase

from bims.utils.geomorphological_zone import get_geomorphological_zone_class


class TestGeomorphologicalZone(TestCase):

    def test_get_geo_class_from_refined_geo(self):
        location_site = LocationSiteF.create(
            refined_geomorphological='Mountain stream'
        )
        self.assertEqual(
            'Upper',
            get_geomorphological_zone_class(location_site)
        )

        location_site = LocationSiteF.create(
            refined_geomorphological='Lower foothill'
        )
        self.assertEqual(
            'Lower',
            get_geomorphological_zone_class(location_site)
        )

    def test_get_geo_class_from_location_context(self):
        location_site = LocationSiteF.create()
        location_context_group = LocationContextGroupF.create(
            name='geo_class',
            key='geo_class'
        )
        LocationContextF.create(
            group=location_context_group,
            site=location_site,
            value='Upper'
        )
        self.assertEqual(
            'Upper',
            get_geomorphological_zone_class(location_site)
        )

        location_context_group_recoded = LocationContextGroupF.create(
            name='geo_class_recoded',
            key='geo_class_recoded'
        )
        location_site_2 = LocationSiteF.create()
        LocationContextF.create(
            group=location_context_group_recoded,
            site=location_site_2,
            value='transitional'
        )
        self.assertEqual(
            'Upper',
            get_geomorphological_zone_class(location_site_2)
        )
