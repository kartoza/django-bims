import csv
import os

from django.test import TestCase
from preferences import preferences

from bims.api_views.checklist import checklist_collection_records, generate_csv_checklist
from bims.models import LocationContext, SiteSetting
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
from bims.utils.site_code import SANPARK_PARK_KEY


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
        group_model = LocationContext._meta.get_field('group').remote_field.model
        self.park_name = 'Addo Elephant National Park'
        self.location_group = group_model.objects.create(
            name=SANPARK_PARK_KEY
        )
        LocationContext.objects.create(
            site=self.collection_record1.site,
            group=self.location_group,
            value=self.park_name,
        )
        site_setting = preferences.SiteSetting
        if not site_setting:
            site_setting = SiteSetting.objects.create()

        if site_setting:
            site_setting.default_data_source = 'sanparks'
            site_setting.save()

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
        self.assertEqual(
            serializer_data['park_or_mpa_name'],
            self.park_name
        )

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

    def test_csv_checklist_includes_park_invasion_columns(self):

        park_name = 'Addo Elephant National Park'

        self.taxonomy.additional_data = {
            **(self.taxonomy.additional_data or {}),
            f'IS_{park_name}': 'Invasive'
        }
        self.taxonomy.save()

        record = BiologicalCollectionRecordF.create(
            taxonomy=self.taxonomy,
            source_collection='sanparks',
        )

        group_model = LocationContext._meta.get_field('group').remote_field.model
        group = group_model.objects.create(name='SANPARKS checklist group')
        LocationContext.objects.create(
            site=record.site,
            group=group,
            value=park_name,
        )

        collection_records = BiologicalCollectionRecord.objects.filter(
            taxonomy=self.taxonomy
        )

        generate_csv_checklist(
            self.download_request,
            module_name='TestModule',
            collection_records=collection_records,
            batch_size=1000
        )

        self.download_request.refresh_from_db()
        csv_file = self.download_request.request_file
        self.assertTrue(os.path.exists(csv_file.path))

        with open(csv_file.path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            expected_header = 'Addo Elephant NP invasion status'
            self.assertIn(expected_header, fieldnames)

            rows = list(reader)
            self.assertGreaterEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row.get(expected_header), 'Invasive')
