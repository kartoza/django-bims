# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from sass.scripts.fbis_user_importer import FbisUserImporter
from sass.scripts.fbis_site_importer import FbisSiteImporter
from sass.scripts.fbis_river_importer import FbisRiverImporter
from sass.scripts.fbis_site_visit_importer import FbisSiteVisitImporter
from sass.scripts.fbis_sass_biotope_importer import FbisSassBiotopeImporter
from sass.scripts.fbis_rate_importer import FbisRateImporter
from sass.scripts.fbis_site_visit_sass_biotope_importer import (
    FbisSiteVisitSassBiotopeImporter
)
from sass.scripts.fbis_taxon_importer import FbisTaxonImporter
from sass.scripts.fbis_taxon_group_importer import FbisTaxonGroupImporter
from sass.scripts.fbis_taxon_abudance_importer import (
    FbisTaxonAbundanceImporter
)
from sass.scripts.fbis_site_visit_biotope_taxon_importer import (
    FbisSiteVisitBiotopeTaxonImporter
)
from sass.scripts.fbis_sass_validation_status_importer import (
    FbisSassValidationStatusImporter
)
from sass.scripts.fbis_site_visit_taxon_importer import (
    FbisSiteVisitTaxonImporter
)


class Command(BaseCommand):
    help = 'Migrate data from fbis database'
    import_scripts = {
        'user': FbisUserImporter,
        'site': FbisSiteImporter,
        'river': FbisRiverImporter,
        'site_visit': FbisSiteVisitImporter,
        'sass_biotope': FbisSassBiotopeImporter,
        'rate': FbisRateImporter,
        'site_visit_sass_biotope': FbisSiteVisitSassBiotopeImporter,
        'taxon_group': FbisTaxonGroupImporter,
        'taxon': FbisTaxonImporter,
        'taxon_abundance': FbisTaxonAbundanceImporter,
        'site_visit_biotope_taxon': FbisSiteVisitBiotopeTaxonImporter,
        'sass_validation_status': FbisSassValidationStatusImporter,
        'site_visit_taxon': FbisSiteVisitTaxonImporter
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--sqlite-file',
            dest='sqlite_file',
            default=None,
            help='Sqlite filename'
        )
        parser.add_argument(
            '-t',
            '--table',
            dest='table_name',
            default=None,
            help='Sqlite table to be imported'
        )
        parser.add_argument(
            '-m',
            '--max-row',
            dest='max_row',
            default=None,
            help='Sqlite max row'
        )

    def handle(self, *args, **options):
        # check if file exists
        sqlite_filename = options.get('sqlite_file', None)
        sqlite_table = options.get('table_name', None)
        sqlite_max_row = options.get('max_row', None)

        if not sqlite_filename:
            print('You need to provide a name for sqlite_filename file')
            return

        if not sqlite_table:
            print('Import all table')
            for table_name in self.import_scripts:
                print('Import %s' % table_name)
                self.import_scripts[table_name](sqlite_filename)
        else:
            sqlite_table = sqlite_table.lower()
            if sqlite_table in self.import_scripts:
                print('Import %s table' % sqlite_table)
                importer = self.import_scripts[sqlite_table](
                    sqlite_filename,
                    max_row=sqlite_max_row
                )
                importer.import_data()
            else:
                print('Table %s not found' % sqlite_table)
