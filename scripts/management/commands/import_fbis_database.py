# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from scripts.importer.fbis_user_importer import FbisUserImporter
from scripts.importer.fbis_site_importer import FbisSiteImporter
from scripts.importer.fbis_river_importer import FbisRiverImporter
from scripts.importer.fbis_site_visit_importer import FbisSiteVisitImporter
from scripts.importer.fbis_sass_biotope_importer import FbisSassBiotopeImporter
from scripts.importer.fbis_rate_importer import FbisRateImporter
from scripts.importer.fbis_site_visit_sass_biotope_importer import (
    FbisSiteVisitSassBiotopeImporter
)
from scripts.importer.fbis_taxon_importer import FbisTaxonImporter
from scripts.importer.fbis_taxon_group_importer import FbisTaxonGroupImporter
from scripts.importer.fbis_taxon_abudance_importer import (
    FbisTaxonAbundanceImporter
)
from scripts.importer.fbis_site_visit_biotope_taxon_importer import (
    FbisSiteVisitBiotopeTaxonImporter
)
from scripts.importer.fbis_sass_validation_status_importer import (
    FbisSassValidationStatusImporter
)
from scripts.importer.fbis_site_visit_taxon_importer import (
    FbisSiteVisitTaxonImporter
)
from scripts.importer.fbis_chem_importer import FbisChemImporter
from scripts.importer.fbis_site_visit_chem_importer import (
    FbisSiteVisitChemImporter
)
from scripts.importer.fbis_user_sass_validation_importer import (
    FbisUserSassValidationImporter
)
from scripts.importer.fbis_biobase_site_importer import FbisBiobaseSiteImporter
from scripts.importer.fbis_biobase_biotope_importer import FbisBiobaseBiotopeImporter
from scripts.importer.fbis_biobase_collection_importer import FbisBiobaseCollectionImporter
from scripts.importer.fbis_biobase_chemical_importer import (
    FbisBiobaseChemicalImporter
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
        'site_visit_taxon': FbisSiteVisitTaxonImporter,
        'chem': FbisChemImporter,
        'site_visit_chem': FbisSiteVisitChemImporter,
        'user_sass_validation': FbisUserSassValidationImporter,
        'biobase_site': FbisBiobaseSiteImporter,
        'biobase_biotope': FbisBiobaseBiotopeImporter,
        'biobase_collections': FbisBiobaseCollectionImporter,
        'biobase_chemical': FbisBiobaseChemicalImporter
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
        parser.add_argument(
            '-d',
            '--database',
            dest='postgres_database',
            default=None,
            help='Postgres database name'
        )
        parser.add_argument(
            '-u',
            '--user',
            dest='postgres_user',
            default=None,
            help='Postgres database user'
        )
        parser.add_argument(
            '-w',
            '--password',
            dest='postgres_password',
            default=None,
            help='Postgres database password'
        )
        parser.add_argument(
            '-host',
            '--host',
            dest='postgres_host',
            default=None,
            help='Postgres database host'
        )

    def handle(self, *args, **options):
        # check if file exists
        sqlite_filename = options.get('sqlite_file', None)
        sqlite_table = options.get('table_name', None)
        sqlite_max_row = options.get('max_row', None)
        postgres_database = options.get('postgres_database', None)
        postgres_user = options.get('postgres_user', None)
        postgres_password = options.get('postgres_password', None)
        postgres_host = options.get('postgres_host', None)

        if not sqlite_filename and not postgres_database:
            print('You need to provide a name for sqlite_filename file or '
                  'postgres database details')
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
                if postgres_database:
                    importer.postgres_database = postgres_database
                    importer.postgres_user = postgres_user
                    importer.postgres_password = postgres_password
                    importer.postgres_host = postgres_host
                importer.import_data()
            else:
                print('Table %s not found' % sqlite_table)
