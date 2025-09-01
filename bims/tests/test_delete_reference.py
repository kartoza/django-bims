# coding=utf-8

from django.test import TestCase
from allauth.utils import get_user_model
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.factories import EntryFactory
from bims.models import BiologicalCollectionRecord
from bims.tests.model_factories import (
    SourceReferenceBibliographyF,
    BiologicalCollectionRecordF
)


class TestEditReference(FastTenantTestCase):
    """ Tests Delete source reference view (AJAX JSON responses) """

    def setUp(self):
        """
        Sets up before each test
        """
        user = get_user_model().objects.create(
            is_staff=True,
            is_active=True,
            is_superuser=True,
            username='@.test'
        )
        user.set_password('psst')
        user.save()

        non_staff_user = get_user_model().objects.create(
            is_staff=False,
            is_active=True,
            is_superuser=False,
            username='@.test2'
        )
        non_staff_user.set_password('psst')
        non_staff_user.save()

        self.client = TenantClient(self.tenant)

        entry = EntryFactory.create(title='Test')
        self.source_reference = SourceReferenceBibliographyF.create(source=entry)

        self.delete_url = '/delete-source-reference/'

    def _login(self):
        resp = self.client.login(username='@.test', password='psst')
        self.assertTrue(resp)

    def test_delete_is_blocked_when_linked_records_exist(self):
        """
        When collection records reference the source reference,
        the view should respond with JSON error (400) and not delete/detach.
        """
        self._login()

        # Create a record linked to the reference
        bio = BiologicalCollectionRecordF.create(source_reference=self.source_reference)

        post_data = {
            'reference_id': self.source_reference.id,
            'next': '/map'
        }
        response = self.client.post(
            self.delete_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # mark as AJAX to get JSON
        )

        # Expect JSON error
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload.get('success'))
        # Be flexible on exact wording; check key phrases
        self.assertIn('linked to collection records', payload.get('message', '').lower())

        # Ensure the record is still linked (no detach)
        bio.refresh_from_db()
        self.assertIsNotNone(bio.source_reference)
        self.assertEqual(bio.source_reference_id, self.source_reference.id)

        # Ensure the reference still exists
        self.source_reference.refresh_from_db()  # no DoesNotExist -> still there

    def test_delete_succeeds_when_no_linked_records(self):
        """
        When there are no linked records, deletion should succeed with JSON 200.
        """
        self._login()

        # Use a fresh reference with no links
        entry = EntryFactory.create(title='Unlinked')
        unlinked_ref = SourceReferenceBibliographyF.create(source=entry)

        post_data = {
            'reference_id': unlinked_ref.id,
            'next': '/map'
        }
        response = self.client.post(
            self.delete_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get('success'))
        self.assertIn('successfully deleted', payload.get('message', '').lower())

        # Confirm deletion
        with self.assertRaises(type(unlinked_ref).DoesNotExist):
            type(unlinked_ref).objects.get(id=unlinked_ref.id)
