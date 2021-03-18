# coding=utf-8

from django.test import TestCase, Client
from allauth.utils import get_user_model
from bims.factories import (
    EntryFactory,
)
from bims.models import (
    BiologicalCollectionRecord
)
from bims.tests.model_factories import (
    SourceReferenceBibliographyF,
    BiologicalCollectionRecordF
)


class TestEditReference(TestCase):
    """ Tests Edit reference view
    """

    def setUp(self):
        """
        Sets up before each test
        """
        user = get_user_model().objects.create(
            is_staff=True,
            is_active=True,
            is_superuser=True,
            username='@.test')
        user.set_password('psst')
        user.save()
        non_staff_user = get_user_model().objects.create(
            is_staff=False,
            is_active=True,
            is_superuser=False,
            username='@.test2')
        non_staff_user.set_password('psst')
        non_staff_user.save()
        self.client = Client()
        entry = EntryFactory.create(
            title='Test'
        )
        self.source_reference = SourceReferenceBibliographyF.create(
            source=entry
        )

    def test_delete_existing_source_reference(self):
        """
        Test delete existing record
        """
        # Login
        resp = self.client.login(
            username='@.test',
            password='psst'
        )
        self.assertTrue(resp)
        bio = BiologicalCollectionRecordF.create(
            source_reference=self.source_reference
        )
        post_data = {
            'reference_id': self.source_reference.id,
            'next': '/map'
        }
        response = self.client.post(
            '/delete-source-reference/',
            post_data,
            follow=True
        )
        bio_record = BiologicalCollectionRecord.objects.get(
            id=bio.id
        )
        self.assertIsNone(
            bio_record.source_reference
        )
        self.assertEqual(
            str(list(response.context['messages'])[0]),
            'Source reference Test successfully deleted!'
        )
