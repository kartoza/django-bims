# coding=utf-8
"""Tests for source reference."""

from django.test import TestCase
from bims.models.source_reference import SourceReference
from bims.tests.model_factories import (
    SourceReferenceF,
    SourceReferenceBibliographyF,
    SourceReferenceDatabaseF,
    DatabaseRecordF,
    BiologicalCollectionRecordF
)
from td_biblio.tests.model_factories import (
    JournalF,
    EntryF
)


class TestSourceReferences(TestCase):
    """ Tests CURD Profile.
    """

    def setUp(self):
        """
        Sets up before each test
        """

        # setup bibliography
        self.journal_title = 'test title'
        self.entry = EntryF.create(
            pk=1,
            title=self.journal_title,
            journal=JournalF.create(
                pk=1,
                name='journal'
            )
        )

        # setup database record
        self.db_name = 'test db'
        self.db_record = DatabaseRecordF(name=self.db_name)

        # setup biological record
        self.record = BiologicalCollectionRecordF()

    def test_source_reference_create(self):
        """
        Tests Source references create
        """
        source = SourceReferenceF(note='test')
        self.assertIsNotNone(source.pk)
        self.assertIsNone(source.get_source_unicode())

        # assign into record
        self.record.source_reference = source
        self.record.save()

        self.assertIsNotNone(self.record.source_reference)
        self.assertIsNone(self.record.source_reference.get_source_unicode())

    def test_source_reference_bibilography(self):
        """
        Tests Source references bibliography create
        """
        source = SourceReferenceBibliographyF(note='test', source=self.entry)
        source_reference = SourceReference.objects.last()
        self.assertEqual(
            source_reference.__class__.__name__,
            source.__class__.__name__
        )
        self.assertEqual(
            source_reference.source.title,
            self.entry.title
        )

        # assign into record
        self.record.source_reference = source
        self.record.save()
        self.assertEqual(
            self.record.source_reference.__class__.__name__,
            source.__class__.__name__
        )
        self.assertEqual(
            self.record.source_reference.source.title,
            self.entry.title
        )

    def test_source_reference_database(self):
        """
        Tests Source references database create
        """
        source = SourceReferenceDatabaseF(
            note='test', source=self.db_record)
        source_reference = SourceReference.objects.last()
        self.assertEqual(
            source_reference.__class__.__name__,
            source.__class__.__name__
        )
        self.assertEqual(
            source_reference.source.name,
            self.db_name
        )

        # assign into record
        self.record.source_reference = source
        self.record.save()
        self.assertEqual(
            self.record.source_reference.__class__.__name__,
            source.__class__.__name__
        )
        self.assertEqual(
            self.record.source_reference.source.name,
            self.db_name
        )
