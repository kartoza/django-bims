import os
import ast
import csv
import re
import logging
from django.db.models import signals, Q
from django.utils.dateparse import parse_date
from django.conf import settings
from scripts.management.csv_command import CsvCommand
from bims.utils.fetch_gbif import (
    fetch_all_species_from_gbif, check_taxa_duplicates
)
from bims.utils.logger import log
from bims.utils.gbif import *
from bims.models.taxonomy import taxonomy_pre_save_handler

logger = logging.getLogger('bims')

IN_GBIF = 'In GBIF'
TAXON = 'Taxon'
SPECIES = 'Species'
GENUS = 'Genus'
FAMILY = 'Family'
ORDER = 'Order'
CLASS = 'Class'
PHYLUM = 'Phylum'
KINGDOM = 'Kingdom'
DIVISION = 'Division'
GROWTH_FORM = 'Growth Form'
SCIENTIFIC_NAME = 'Scientific name and authority'
FORMER_SPECIES_NAME = 'Former scientific name'

TAXON_RANKS = [
    PHYLUM,
    CLASS,
    ORDER,
    FAMILY,
    GENUS,
]
ALL_TAXON_RANKS = [
    'KINGDOM',
    'PHYLUM',
    'CLASS',
    'ORDER',
    'FAMILY',
    'GENUS',
    'SPECIES'
]


class Command(CsvCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--import-date',
            dest='import_date',
            default=None,
            help='Date of the import (YYYY-MM-DD)'
        )
        parser.add_argument(
            '-c',
            '--check-data',
            dest='check_only',
            default='False',
            help='Checking the data only'
        )
        parser.add_argument(
            '-m',
            '--import-missing',
            dest='missing_only',
            default='False',
            help='Only ingest missing data'
        )
        parser.add_argument(
            '-e',
            '--export-to-csv',
            dest='csv_name',
            default='',
            help='Export to csv name'
        )

    def init(self, options):
        self.import_date = options.get('import_date', None)
        try:
            self.check_only = ast.literal_eval(
                options.get('check_only')
            )
        except ValueError:
            self.check_only = False
        try:
            self.missing_only = ast.literal_eval(
                options.get('missing_only')
            )
        except ValueError:
            self.missing_only = False
        self.csv_name = options.get('csv_name')

    def csv_file_name(self, options):
        return 'SA Algal Master List FBISv3_3 Mar 2020.csv'

    @property
    def csv_root_folder(self):
        dev_folder = '/home/web/django_project'
        folder_name = 'data'
        if os.path.exists(dev_folder):
            root = dev_folder
        else:
            root = '/usr/src/bims'
        return os.path.join(
            root,
            'scripts/static/{}/'.format(
                folder_name
            )
        )

    def row_value(self, row, key):
        """
        Get row value by key
        :param row: row data
        :param key: key
        :return: row value
        """
        row_value = row[key]
        row_value = row_value.replace('\xa0', ' ')
        row_value = row_value.replace('\xc2', '')
        row_value = row_value.replace('\\xa0', '')
        row_value = row_value.strip()
        row_value = re.sub(' +', ' ', row_value)
        return row_value

    def get_taxonomy(self, taxon_name, scientific_name, rank):
        """
        Get taxonomy from database and gbif
        :param taxon_name: name of the taxon
        :param scientific_name: scientific name of the taxon
        :param rank: rank of the taxon
        :return: taxonomy object
        """
        taxon_data = Taxonomy.objects.filter(
            Q(canonical_name__iexact=taxon_name) |
            Q(legacy_canonical_name__icontains=taxon_name),
            rank=rank
        )
        if not taxon_data.exists():
            parent = fetch_all_species_from_gbif(
                species=taxon_name,
                taxonomic_rank=rank,
                should_get_children=False,
                fetch_vernacular_names=False
            )
            if parent:
                if taxon_name.lower() not in parent.scientific_name.lower():
                    parent.scientific_name = scientific_name
                    parent.legacy_canonical_name = taxon_name
                    parent.canonical_name = taxon_name
                    parent.gbif_key = ''
                    parent.gbif_data = {}
                    parent.save()
            else:
                parent, _ = Taxonomy.objects.get_or_create(
                    canonical_name=taxon_name,
                    scientific_name=scientific_name,
                    legacy_canonical_name=taxon_name
                )
        else:
            parent = taxon_data[0]
        return parent

    def validate_parents(self, taxon, row):
        """
        Validating parent data from taxon,
        cross-check between parents of the database and parents of CSV.
        If the parent has a different value, update to the correct parent.
        :param taxon: Taxonomy object
        :param row: csv row data
        """
        parent = taxon.parent
        while parent:
            try:
                csv_data = self.row_value(row, str(parent.rank).capitalize())
            except KeyError:
                parent = parent.parent
                continue
            parent_rank = self.parent_rank(taxon.rank)
            if (
                    csv_data not in parent.canonical_name and
                    csv_data not in parent.legacy_canonical_name or
                    str(parent.rank).upper() != parent_rank
            ):
                print('Different parent for {}'.format(str(taxon)))
                parent_taxon = self.get_parent(
                    row, current_rank=parent_rank.capitalize())
                print('Updated to {}'.format(str(parent_taxon)))
                taxon.parent = parent_taxon
                taxon.save()
            taxon = parent
            parent = parent.parent
        print('Parents has been validated')

    def get_parent(self, row, current_rank=GENUS):
        taxon = self.get_taxonomy(
            self.row_value(row, current_rank),
            self.row_value(row, current_rank),
            current_rank.upper()
        )
        if not taxon.gbif_key or not taxon.parent:
            ranks = TAXON_RANKS
            try:
                ranks.remove(current_rank)
            except ValueError as e:
                print(current_rank)
                return
            if len(ranks) > 0:
                parent = self.get_parent(row, ranks[len(ranks)-1])
                taxon.parent = parent
                taxon.save()
        return taxon

    def additional_data(self, taxonomy, row):
        """
        Import additional data from CSV into taxonomy.
        :param taxonomy: Taxonomy object
        :param row: data row from csv
        """
        pass

    def rank_classifier(self):
        """
        If we just want to return species with Kingdom animalia,
        return '{"kingdom": "animalia"}'
        """
        return {}

    def csv_dict_reader(self, csv_reader):
        signals.pre_save.disconnect(
            taxonomy_pre_save_handler,
            sender=Taxonomy
        )
        errors = []
        success = []
        csv_data = []

        index = 1

        for row in csv_reader:
            index += 1
            taxon_name = self.row_value(row, TAXON)
            if SCIENTIFIC_NAME in row:
                scientific_name = (self.row_value(row, SCIENTIFIC_NAME)
                                if self.row_value(row, SCIENTIFIC_NAME)
                                else taxon_name)
            else:
                scientific_name = taxon_name
            scientific_name = scientific_name.strip()
            # Get rank
            if self.row_value(row, SPECIES):
                rank = SPECIES
            elif self.row_value(row, GENUS):
                rank = GENUS
            elif self.row_value(row, FAMILY):
                rank = FAMILY
            elif self.row_value(row, ORDER):
                rank = ORDER
            elif self.row_value(row, CLASS):
                rank = CLASS
            elif self.row_value(row, PHYLUM):
                rank = PHYLUM
            else:
                rank = KINGDOM
            taxa = Taxonomy.objects.filter(
                Q(canonical_name__iexact=taxon_name) |
                Q(legacy_canonical_name__icontains=taxon_name),
                rank=rank.upper()
            )
            print('---------')
            ids = []

            if self.check_only:
                print('Checking data {}'.format(taxon_name))
                if not taxa.exists():
                    errors.append(
                        'Missing taxon {taxon} - {row}'.format(
                            taxon=taxon_name,
                            row=index
                        )
                    )
                else:
                    if taxa.count() > 1:
                        errors.append(
                            'Duplicate taxa for {taxon} - {row}'.format(
                                taxon=taxon_name,
                                row=index
                            )
                        )
                        check_taxa_duplicates(
                            taxon_name,
                            rank
                        )
                    if taxa[0].id not in ids:
                        ids.append(taxa[0].id)
                    else:
                        errors.append(
                            'Duplicate ids for {taxon} - {row}'.format(
                                taxon=taxon_name,
                                row=index
                            )
                        )
                continue

            try:
                taxonomy = None
                if self.missing_only and taxa.exists():
                    logger.debug(
                        'Skip ingesting existing data {}'.format(taxon_name))
                    continue
                if taxa.exists():
                    taxonomy = taxa[0]
                    logger.debug('{} already in the system'.format(
                        taxon_name
                    ))
                suspicious_gbif_data = False
                if taxonomy:
                    gbif_key = taxonomy.gbif_key
                    if gbif_key:
                        if taxonomy.taxonomic_status == 'SYNONYM':
                            suspicious_gbif_data = True
                            taxonomy = None
                if suspicious_gbif_data:
                    logger.debug(
                        'Suspicious data found, re-fetching'
                    )
                if not taxonomy:
                    # Fetch from gbif
                    taxonomy = fetch_all_species_from_gbif(
                        species=taxon_name,
                        taxonomic_rank=rank,
                        should_get_children=False,
                        fetch_vernacular_names=False,
                        use_name_lookup=True,
                        **self.rank_classifier()
                    )
                if taxonomy:
                    success.append(taxonomy.id)
                else:
                    # Try again with lookup
                    logger.debug('Use different method')
                    taxonomy = fetch_all_species_from_gbif(
                        species=taxon_name,
                        taxonomic_rank=rank,
                        should_get_children=False,
                        fetch_vernacular_names=False,
                        use_name_lookup=False,
                        **self.rank_classifier()
                    )
                    if not taxonomy:
                        errors.append({
                            'row': index,
                            'error': 'Taxonomy not found'
                        })
                    else:
                        success.append(taxonomy.id)

                # Validate data
                if taxonomy:
                    if (taxon_name not in taxonomy.scientific_name and
                        taxon_name.lower().strip() !=
                        taxonomy.canonical_name.lower().strip() and
                        taxon_name.lower() not in taxonomy.legacy_canonical_name.lower()
                    ):
                        taxonomy = None
                    else:
                        if not taxonomy.parent:
                            taxonomy.parent = self.get_parent(row)

                # Data from GBIF couldn't be found, so add it manually
                if not taxonomy:
                    parent = self.get_parent(row)
                    if not parent:
                        errors.append({
                            'row': index,
                            'error': 'Parent not found {}'.format(
                                taxon_name
                            )
                        })
                    else:
                        # Taxonomy not found, create one
                        taxonomy, _ = Taxonomy.objects.get_or_create(
                            scientific_name=scientific_name,
                            canonical_name=taxon_name,
                            rank=TaxonomicRank[rank.upper()].name,
                            parent=parent
                        )
                        success.append(taxonomy.id)

                # -- Finish
                if taxonomy:
                    # Merge taxon with same canonical name
                    legacy_canonical_name = taxonomy.legacy_canonical_name
                    legacy_canonical_name = legacy_canonical_name.replace('\\xa0', '')
                    preferred_taxon = check_taxa_duplicates(
                        taxon_name,
                        taxonomy.rank
                    )
                    if preferred_taxon:
                        taxonomy = preferred_taxon
                    if FORMER_SPECIES_NAME in row:
                        former_species_name = self.row_value(
                            row, FORMER_SPECIES_NAME)
                        if len(former_species_name) > 500:
                            former_species_name = former_species_name[:500]
                        if former_species_name not in legacy_canonical_name:
                            legacy_canonical_name += ';' + former_species_name
                    taxonomy.legacy_canonical_name = legacy_canonical_name[:700]
                    # -- Import date
                    if self.import_date:
                        taxonomy.import_date = parse_date(self.import_date)
                    self.additional_data(
                        taxonomy,
                        row
                    )

                    # Add to csv data
                    if self.csv_name:
                        csv_data.append(
                            self.process_csv_data(taxonomy)
                        )

                # -- Validate parents
                self.validate_parents(
                    taxon=taxonomy,
                    row=row
                )

            except Exception as e:  # noqa
                print(str(e))
                errors.append({
                    'row': index,
                    'error': str(e)
                })

        if len(errors) > 0: logger.debug(errors)
        log('----')
        if len(success) > 0: logger.debug(success)
        if self.csv_name:
            self.export_to_csv(csv_data)

    def process_csv_data(self, taxon):
        data = {}
        current_taxon = taxon
        if current_taxon.rank in ALL_TAXON_RANKS:
            data[current_taxon.rank] = taxon.canonical_name
        while current_taxon.parent:
            current_taxon = current_taxon.parent
            if current_taxon.rank in ALL_TAXON_RANKS:
                data[current_taxon.rank] = (
                    current_taxon.canonical_name.encode('utf-8')
                )

        # sort by rank
        csv_data = []
        for rank in ALL_TAXON_RANKS:
            csv_data.append(data[rank] if rank in data else '-')

        csv_data.append(taxon.canonical_name.encode('utf-8'))
        csv_data.append(taxon.scientific_name.encode('utf-8'))
        csv_data.append('https://gbif.org/species/{}'.format(
            taxon.gbif_key) if
                        taxon.gbif_key else '-')
        return csv_data

    def export_to_csv(self, csv_data):
        csv_path = os.path.join(settings.MEDIA_ROOT, 'taxa_csv')
        if not os.path.exists(csv_path): os.mkdir(csv_path)
        csv_file_path = os.path.join(csv_path, '{t}.csv'.format(
            t=self.csv_name
        ))
        with open(csv_file_path, mode='w') as csv_file:
            writer = csv.writer(
                csv_file, delimiter=',', quotechar='"',
                quoting=csv.QUOTE_MINIMAL)
            writer.writerow([
                'Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus',
                'Species', 'Taxon', 'Scientific name & Authority', 'GBIF url'])

            for data in csv_data:
                writer.writerow(data)

    def parent_rank(self, rank):
        """
        Return rank of parent
        :param rank: current rank
        :return: rank of parent
        """
        try:
            return ALL_TAXON_RANKS[ALL_TAXON_RANKS.index(rank.upper())-1]
        except KeyError:
            return 'KINGDOM'
