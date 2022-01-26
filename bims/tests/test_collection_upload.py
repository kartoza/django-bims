import os
import mock
from django.test import TestCase
from bims.scripts.collections_upload_source_reference import (
    process_source_reference
)
from bims.tests.model_factories import (
    DocumentF,
    UserF
)

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


def mocked_doi_loader(
        ids = None, format = "bibtex", style = 'apa',
        locale = "en-US", url = None, **kwargs):
    response_file = 'doi_data.json'
    response_path = os.path.join(
        test_data_directory, response_file)
    if os.path.exists(response_path):
        response_data = open(response_path)
        json_data = response_data.read()
        response_data.close()
        return json_data
    return ''


class TestCollectionUpload(TestCase):
    document_link = 'site/document/11'
    owner = None
    reference_title = 'title'

    def setUp(self):
        self.owner = UserF.create(
            first_name='dimas'
        )

    def test_reference_missing_author(self):
        # Missing author
        message, source_reference = process_source_reference(
            reference='name',
            document_link=self.document_link,
            reference_category='published report'
        )
        self.assertTrue('missing author' in message.lower())

    def test_reference_document_not_exist(self):
        message, source_reference = process_source_reference(
            document_author='dimas',
            reference='name',
            document_link=self.document_link,
            reference_category='published report'
        )
        self.assertTrue('does not exist' in message)

    def test_reference_published_report_created(self):
        # Published report source reference created
        DocumentF.create(
            id=11,
            owner=self.owner,
            title=self.reference_title
        )
        message, source_reference = process_source_reference(
            document_author='dimas',
            reference=self.reference_title,
            document_link=self.document_link,
            reference_category='published report'
        )
        self.assertIsNotNone(source_reference)
        self.assertEqual(
            source_reference.source_name,
            self.reference_title
        )
        self.assertEqual(
            source_reference.title,
            self.reference_title
        )

    def test_reference_bibliography_not_created(self):
        message, source_reference = process_source_reference(
            document_author=self.owner.first_name,
            reference=self.reference_title,
            doi='1123',
            reference_category='peer-reviewed'
        )
        self.assertIsNone(
            source_reference
        )

    @mock.patch('habanero.cn.content_negotiation', mock.Mock(
        side_effect=mocked_doi_loader))
    def test_reference_bibliography_created(self):
        doc = DocumentF.create(
            id=11,
            owner=self.owner,
            title=self.reference_title
        )
        message, source_reference = process_source_reference(
            document_link=self.document_link,
            document_author=self.owner.first_name,
            reference=self.reference_title,
            doi='10.1016/j.aaen.2007.05.002',
            reference_category='peer-reviewed'
        )
        self.assertIsNotNone(
            source_reference
        )
        self.assertEqual(
            source_reference.document,
            doc
        )

    def test_reference_database_created(self):
        message, source_reference = process_source_reference(
            document_author=self.owner.first_name,
            reference=self.reference_title,
            source_year='2012',
            reference_category='database'
        )
        self.assertIsNotNone(
            source_reference
        )
