import csv
import os
import tempfile

from django_tenants.test.cases import FastTenantTestCase

from bims.enums.taxon_addendum import TaxonAddendum
from bims.tasks.download_taxa_list import process_download_csv_taxa_list
from bims.tests.model_factories import TaxonomyF


class TestDownloadTaxaListAddendumColumn(FastTenantTestCase):

    def setUp(self):
        self.csv_file = tempfile.NamedTemporaryFile(
            suffix='.csv', delete=False
        )
        self.csv_file.close()

    def tearDown(self):
        if os.path.exists(self.csv_file.name):
            os.remove(self.csv_file.name)

    def _read_header_row(self):
        with open(self.csv_file.name, newline='') as f:
            reader = csv.reader(f)
            return next(reader)

    def test_addendum_column_hidden_when_no_addendum_data(self):
        taxon = TaxonomyF.create(
            scientific_name='Homo sapiens L.',
            canonical_name='Homo sapiens',
            author='L.',
        )
        process_download_csv_taxa_list(
            request={},
            csv_file_path=self.csv_file.name,
            filename='taxa.csv',
            user_id=None,
            taxa_ids=[taxon.id],
        )
        self.assertNotIn('Addendum', self._read_header_row())

    def test_addendum_column_shown_when_addendum_data_present(self):
        taxon = TaxonomyF.create(
            scientific_name='Aquanothrus montanus Engelbrecht, 1975',
            canonical_name='Aquanothrus montanus',
            author='Engelbrecht, 1975',
            addendum=TaxonAddendum.SENSU_LATO.name,
        )
        process_download_csv_taxa_list(
            request={},
            csv_file_path=self.csv_file.name,
            filename='taxa.csv',
            user_id=None,
            taxa_ids=[taxon.id],
        )
        self.assertIn('Addendum', self._read_header_row())
