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
from bims.serializers.bio_collection_serializer import BioCollectionOneRowSerializer


class TestCollectionRecordView(FastTenantTestCase):

    def setUp(self):
        self.client = TenantClient(self.tenant)

    def test_common_user_delete_collection_record(self):
        """Test common user deleting collection record"""
        user = UserF.create()
        self.client.login(
            username=user.username,
            password='password'
        )
        col = BiologicalCollectionRecordF.create()
        response = self.client.post(
            reverse('collection-delete', kwargs={
                'col_id': col.id
            })
        )
        self.assertEqual(
            response.status_code,
            403
        )
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(
                id=col.id).exists())

    def test_super_user_delete_collection_record(self):
        user = UserF.create(is_superuser=True)
        self.client.login(
            username=user.username,
            password='password'
        )
        col = BiologicalCollectionRecordF.create()
        response = self.client.post(
            '{url}?next={next}'.format(
                url=reverse('collection-delete', kwargs={
                    'col_id': col.id
                }),
                next=reverse('site-visit-list')
            )
        )
        self.assertEqual(
            response.url,
            reverse('site-visit-list')
        )
        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(id=col.id).exists())

    def test_owner_collector_user_delete_collection_record(self):
        """Test owner or collector user deleting collection record"""
        user = UserF.create()
        self.client.login(
            username=user.username,
            password='password'
        )
        col = BiologicalCollectionRecordF.create(
            owner=user
        )
        self.client.post(
            reverse('collection-delete', kwargs={
                'col_id': col.id
            })
        )
        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(id=col.id).exists())

        # Collector
        col = BiologicalCollectionRecordF.create(
            collector_user=user
        )
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(id=col.id).exists())
        self.client.post(
            reverse('collection-delete', kwargs={
                'col_id': col.id
            })
        )
        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(id=col.id).exists())



class TestBioCollectionOneRowSerializerGeoContext(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.old_keys = preferences.GeocontextSetting.geocontext_keys
        preferences.GeocontextSetting.geocontext_keys = (
            "geo_class_recoded,feow_hydrosheds:h1"
        )

        self.user = UserF.create()
        self.collection = BiologicalCollectionRecordF.create(owner=self.user)

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

    def tearDown(self):
        preferences.GeocontextSetting.geocontext_keys = self.old_keys
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
