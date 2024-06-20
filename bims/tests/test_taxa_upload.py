import os

from django.core.files import File
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from mock import mock

from bims.models import TaxonGroupTaxonomy
from bims.scripts.taxa_upload import TaxaCSVUpload
from bims.tests.model_factories import (
    UploadSessionF,
    TaxonGroupF,
    UserF,
    TaxonomyF,
    Taxonomy,
    VernacularName
)

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


class TestTaxaUpload(FastTenantTestCase):

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.taxon_group = TaxonGroupF.create()
        self.owner = UserF.create(
            first_name='tester'
        )
        self.taxonomy = TaxonomyF.create()

        with open(os.path.join(
            test_data_directory, 'taxa_upload_family.csv'
        ), 'rb') as file:
            self.upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload.fetch_all_species_from_gbif')
    def test_taxa_upload(self, mock_fetch_all_species_from_gbif, mock_finish):
        mock_finish.return_value = None
        mock_fetch_all_species_from_gbif.return_value = self.taxonomy

        taxa_csv_upload = TaxaCSVUpload()
        taxa_csv_upload.upload_session = self.upload_session
        taxa_csv_upload.start('utf-8-sig')

        self.assertTrue(
            Taxonomy.objects.filter(
                canonical_name__icontains='Ecnomidae2',
                taxonomic_status='synonym'
            ).exists()
        )

        self.assertTrue(
            VernacularName.objects.filter(
                name='test1',
                taxonomy__canonical_name__icontains='Ecnomidae2'
            )
        )

        self.assertTrue(
            Taxonomy.objects.get(
                canonical_name='Ecnomidae'
            ).tags.filter(
                name='lentic'
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.get(
                canonical_name='Ecnomidae'
            ).tags.filter(
                name='Lakes'
            ).exists()
        )

        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy__canonical_name='Ecnomidae',
                taxongroup=self.taxon_group,
                is_validated=True
            ).exists()
        )

    @mock.patch('bims.scripts.data_upload.DataCSVUpload.finish')
    @mock.patch('bims.scripts.taxa_upload.fetch_all_species_from_gbif')
    def test_taxa_upload_variety_and_forma(self, mock_fetch_all_species_from_gbif, mock_finish):
        mock_finish.return_value = None
        mock_fetch_all_species_from_gbif.return_value = self.taxonomy

        with open(os.path.join(
                test_data_directory, 'variety_forma_example.csv'
        ), 'rb') as file:
            upload_session = UploadSessionF.create(
                uploader=self.owner,
                process_file=File(file),
                module_group=self.taxon_group
            )

        taxa_csv_upload = TaxaCSVUpload()
        taxa_csv_upload.upload_session = upload_session
        taxa_csv_upload.start('utf-8-sig')

        self.assertTrue(
            Taxonomy.objects.filter(
                rank='VARIETY'
            ).exists()
        )

        self.assertTrue(
            Taxonomy.objects.filter(
                rank='FORMA'
            ).exists()
        )
