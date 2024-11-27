from django.test import TestCase

from bims.api_views.checklist import checklist_collection_records
from bims.models.dataset import Dataset
from bims.models.download_request import DownloadRequest
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.serializers.checklist_serializer import (
    get_dataset_occurrences, ChecklistPDFSerializer, ChecklistSerializer
)
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    TaxonomyF,
    DatasetF,
    VernacularNameF,
    SourceReferenceF,
    TaxonGroupF,
    UserF
)


class TestGetDatasetOccurrences(TestCase):

    def setUp(self):
        # Create datasets for testing
        self.dataset1 = DatasetF.create(
            uuid='123e4567-e89b-12d3-a456-426614174000',
            abbreviation='Dataset 1',
            name='Test Dataset 1'
        )
        source_reference_1 = SourceReferenceF.create(
            note='test',
        )
        self.dataset2 = DatasetF.create(
            uuid='123e4567-e89b-12d3-a456-426614174001',
            name='Test Dataset 2'
        )
        self.dataset3 = DatasetF.create(
            uuid='123e4567-e89b-12d3-a456-426614174002',
            abbreviation='Dataset 3',
            name='Test Dataset 3'
        )

        vernacular_name = VernacularNameF.create(
            name='Test Common Name',
            language='en'
        )

        # Create a taxonomy object
        self.taxonomy = TaxonomyF.create(
            scientific_name='Test Species',
            canonical_name='Test Common Name',
            rank='SPECIES',
            vernacular_names=(vernacular_name,)
        )

        self.collection_record1 = BiologicalCollectionRecordF.create(
            taxonomy=self.taxonomy,
            source_collection='gbif',
            additional_data={
                'datasetKey': '123e4567-e89b-12d3-a456-426614174000',
                'datasetName': 'Test Dataset 1'
            }
        )
        self.collection_record2 = BiologicalCollectionRecordF.create(
            taxonomy=self.taxonomy,
            source_reference=source_reference_1,
            additional_data={
                'datasetKey': '123e4567-e89b-12d3-a456-426614174003',
                'datasetName': 'Nonexistent Dataset',
                'Citation': 'Test Citation'
            }
        )
        self.collection_record3 = BiologicalCollectionRecordF.create(
            taxonomy=self.taxonomy,
            source_reference=source_reference_1,
            additional_data={
                'datasetName': 'Standalone Dataset',
                'Citation': 'Test Citation'
            }
        )
        self.context = {
            'collection_records': BiologicalCollectionRecord.objects.all()
        }
        self.download_request = DownloadRequest.objects.create(
            dashboard_url="http://example.com/dashboard",
            resource_type="csv",
            processing=True,
            rejected=False
        )

    def test_get_dataset_occurrences_with_dataset_keys(self):
        occurrences = BiologicalCollectionRecord.objects.filter(
            additional_data__has_key='datasetKey'
        )
        dataset_names = get_dataset_occurrences(occurrences)

        # Test that the returned dataset names are correct
        self.assertIn('Dataset 1', dataset_names)
        self.assertIn('123e4567-e89b-12d3-a456-426614174003', dataset_names)
        self.assertNotIn('Dataset 2', dataset_names)

    def test_get_dataset_occurrences_without_dataset_keys(self):
        occurrences = BiologicalCollectionRecord.objects.filter(
            additional_data__has_key='datasetName'
        ).exclude(additional_data__has_key='datasetKey')
        dataset_names = get_dataset_occurrences(occurrences)

        # Test that the returned dataset names are correct
        self.assertIn('Standalone Dataset', dataset_names)
        self.assertNotIn('Test Dataset 1', dataset_names)

    def test_get_dataset_occurrences_with_empty_occurrences(self):
        occurrences = BiologicalCollectionRecord.objects.none()
        dataset_names = get_dataset_occurrences(occurrences)

        # Test that the result is an empty list
        self.assertEqual(dataset_names, [])

    def test_pdf_serializer(self):
        serializer = ChecklistPDFSerializer(
            instance=self.taxonomy,
            context=self.context,
            many=False)
        serializer_data = serializer.data
        scientific_name = serializer_data['scientific_name']
        self.assertEqual(scientific_name, 'Test Species')
        self.assertIn('Test Citation', serializer_data['sources'])
        self.assertIn('Dataset 1', serializer_data['sources'])
        self.assertIn('123e4567-e89b-12d3-a456-426614174003', serializer_data['sources'])
        self.assertTrue(Dataset.objects.filter(
            citation='Test Citation'
        ).exists())

    def test_csv_serializer(self):
        serializer = ChecklistSerializer(
            instance=self.taxonomy,
            context=self.context,
            many=False)
        serializer_data = serializer.data
        scientific_name = serializer_data['scientific_name']
        self.assertEqual(scientific_name, 'Test Species')
        self.assertIn('Test Citation', serializer_data['sources'])
        self.assertTrue(Dataset.objects.filter(
            citation='Test Citation'
        ).exists())

    def test_checklist_collection_records(self):
        taxon_group = TaxonGroupF.create()
        UserF.create(is_superuser=True)
        BiologicalCollectionRecordF.create(
            module_group=taxon_group,
            data_type='private'
        )
        BiologicalCollectionRecordF.create(
            module_group=taxon_group,
            data_type='public'
        )
        BiologicalCollectionRecordF.create(
            module_group=taxon_group,
            data_type='sensitive'
        )
        dashboard_url = (
            '/map/#site-detail/taxon=&search=&siteId=&collector=&category=&yearFrom=&yearTo=&months=&boundary=&userBoundary=&' +
            f'referenceCategory=&spatialFilter=&reference=&endemic=&invasions=&conservationStatus=[]&modules={taxon_group.id}&validated=&' +
            'sourceCollection=&module=occurrence&ecologicalCategory=&rank=&siteIdOpen=&orderBy=name&polygon=&dst=&ecosystemType='
        )
        download_request = DownloadRequest.objects.create(
            resource_type='csv',
            resource_name='checklist',
            dashboard_url=dashboard_url
        )
        collection_records = checklist_collection_records(download_request)
        self.assertEqual(
            collection_records.count(),
            3
        )
