# coding=utf-8

from django.test import TestCase, Client
from allauth.utils import get_user_model
from bims.factories import (
    EntryFactory,
    AuthorEntryRankFactory
)
from bims.models import (
    SourceReference,
    BiologicalCollectionRecord
)
from bims.tests.model_factories import (
    SourceReferenceBibliographyF,
    SourceReferenceF,
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

    def test_staff_open_edit_reference_page(self):
        """
        Test edit reference form get method
        """
        # Login
        resp = self.client.login(
            username='@.test',
            password='psst'
        )
        self.assertTrue(resp)
        response = self.client.get(
            '/edit-source-reference/{}/'.format(
                self.source_reference.id
            )
        )
        self.assertEqual(
            self.source_reference.source.title,
            response.context_data['object'].title
        )

    def test_nonstaff_open_edit_reference_page(self):
        resp = self.client.login(
            username='@.test2',
            password='psst'
        )
        self.assertTrue(resp)
        response = self.client.get(
            '/edit-source-reference/{}/'.format(
                self.source_reference.id
            )
        )
        self.assertEqual(
            response.status_code,
            403
        )

    def test_unpublished_data(self):
        self.client.login(
            username='@.test',
            password='psst'
        )
        source_reference_1 = SourceReferenceF.create(
            note='test',
        )
        BiologicalCollectionRecordF.create(
            source_reference=source_reference_1
        )
        BiologicalCollectionRecordF.create(
            source_reference=source_reference_1
        )
        source_reference_2 = SourceReferenceF.create(
            note='test2'
        )
        BiologicalCollectionRecordF.create(
            source_reference=source_reference_2
        )
        source_reference_3 = SourceReferenceF.create(
            note='test2'
        )
        BiologicalCollectionRecordF.create(
            source_reference=source_reference_3
        )
        # Update first source reference
        post_dict = {
            'title': 'updated test'
        }
        self.client.post(
            '/edit-source-reference/{}/'.format(
                source_reference_1.id
            ),
            post_dict
        )
        updated_reference = SourceReference.objects.get(
            id=source_reference_1.id
        )
        self.assertEqual(updated_reference.note, post_dict['title'])
        self.assertEqual(BiologicalCollectionRecord.objects.filter(
            source_reference=updated_reference
        ).count(), 2)

        # Merge source reference 1 with source reference 2
        post_dict['title'] = 'test2'
        self.client.post(
            '/edit-source-reference/{}/'.format(
                source_reference_1.id
            ),
            post_dict
        )
        updated_reference = SourceReference.objects.filter(
            note='test2'
        )[0]
        self.assertEqual(updated_reference.note, post_dict['title'])
        self.assertEqual(BiologicalCollectionRecord.objects.filter(
            source_reference=updated_reference
        ).count(), 4)


    def test_edit_bibliography(self):
        self.client.login(
            username='@.test',
            password='psst'
        )
        first_author = AuthorEntryRankFactory.create(
            entry=self.source_reference.source,
            rank=1
        )
        second_author = AuthorEntryRankFactory.create(
            entry=self.source_reference.source,
            rank=2
        )
        post_dict = {
            'title': 'updated bibliography',
            'year': 2000,
            # Switch authors order
            'author_id_1': (
                second_author.author.user.id
            ),
            'author_id_2': (
                first_author.author.user.id
            ),
            # change journal name
            'source': 'new journal name'
        }
        response = self.client.post(
            '/edit-source-reference/{}/'.format(
                self.source_reference.id
            ),
            post_dict
        )
        updated_reference = SourceReference.objects.get(
            id=self.source_reference.id
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(updated_reference.title, post_dict['title'])
        self.assertEqual(updated_reference.year, post_dict['year'])
        self.assertEqual(
            updated_reference.source.first_author, second_author.author)
        self.assertEqual(
            updated_reference.source.last_author, first_author.author)
        self.assertEqual(
            updated_reference.source.journal.name,
            post_dict['source']
        )
