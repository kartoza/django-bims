from django.test import TestCase
from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from preferences import preferences

from bims.tests.model_factories import (
    UserF,
    BiologicalCollectionRecordF,
    LocationContextGroupF,
    LocationContextF
)
from bims.models import BiologicalCollectionRecord
from bims.models.location_context_filter import LocationContextFilter
from bims.models.location_context_filter_group_order import LocationContextFilterGroupOrder
from bims.serializers.bio_collection_serializer import BioCollectionOneRowSerializer


class TestBioCollectionOneRowSerializerGeoContext(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        geocontext_setting = preferences.GeocontextSetting

        if not geocontext_setting:
            geocontext_setting = preferences.GeocontextSetting.objects.create()

        if geocontext_setting:
            geocontext_setting.geocontext_keys = "geo_class_recoded,feow_hydrosheds:h1"
            geocontext_setting.save()

        self.user = UserF.create()
        self.collection = BiologicalCollectionRecordF.create(
            owner=self.user,
        )

        self.grp1 = LocationContextGroupF.create(
            name="Geomorphology",
            key="geo_class_recoded",
            geocontext_group_key="geo_class_recoded"
        )
        self.grp2 = LocationContextGroupF.create(
            name="Freshwater",
            key="feow_hydrosheds",
            geocontext_group_key="feow_hydrosheds",
            layer_identifier="h1"
        )

        LocationContextF.create(
            site=self.collection.site, group=self.grp1, value="GMZ1"
        )
        LocationContextF.create(
            site=self.collection.site, group=self.grp2, value="FW1"
        )

        ctx_filter = LocationContextFilter.objects.create(
            title="Test Filter", display_order=1
        )
        LocationContextFilterGroupOrder.objects.create(
            group=self.grp1, filter=ctx_filter, group_display_order=1
        )
        LocationContextFilterGroupOrder.objects.create(
            group=self.grp2, filter=ctx_filter, group_display_order=2
        )

    def tearDown(self):
        super().tearDown()

    def test_serializer_includes_geocontext_columns(self):
        """Serializer should add the GeoContext columns and values."""
        serializer = BioCollectionOneRowSerializer(
            self.collection,
            context={"header": []}
        )
        data = serializer.data

        self.assertIn("Geomorphology", data)
        self.assertIn("Freshwater", data)

        self.assertEqual(data["Geomorphology"], "GMZ1")
        self.assertEqual(data["Freshwater"], "FW1")

        self.assertIn("Geomorphology", serializer.context["header"])
        self.assertIn("Freshwater", serializer.context["header"])
