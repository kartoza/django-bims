from django.test import TestCase
from django.urls import reverse

from bims.tests.model_factories import (
    UserF,
    BiologicalCollectionRecordF
)
from bims.models import BiologicalCollectionRecord



class TestCollectionRecordView(TestCase):

    def setUp(self):
        pass

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
                next=reverse('nonvalidated-user-list')
            )
        )
        self.assertEqual(
            response.url,
            reverse('nonvalidated-user-list')
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
