import csv
import re
import copy
import logging
from django.contrib.sites.models import Site
from bims.scripts.species_keys import *
from bims.enums import TaxonomicRank
from bims.models import (
    Taxonomy,
    TaxaUploadSession
)
from bims.utils.fetch_gbif import (
    fetch_all_species_from_gbif
)

logger = logging.getLogger('bims')


class TaxaCSVUpload(object):

    taxa_upload_session = TaxaUploadSession.objects.none()
    error_list = []
    success_list = []
    headers = []
    total_rows = 0
    domain = ''

    def import_taxa(self):
        """
        Import taxa list from csv file
        """
        self.error_list = []
        self.success_list = []
        self.domain = Site.objects.get_current().domain
        self.total_rows = len(
            self.taxa_upload_session.process_file.readlines()
        ) - 1
        with open(self.taxa_upload_session.process_file.path) as csv_file:
            self.species_csv_dict_reader(csv.DictReader(csv_file))

    def error_file(self, error_row, error_message):
        """
        Write to error file
        :param error_row: error data
        :param error_message: error message for this row
        """
        logger.log(
            level=logging.ERROR,
            msg=str(error_message)
        )
        error_row['error_message'] = error_message
        self.error_list.append(error_row)

    def success_file(self, success_row, taxon_id):
        """
        Write to success file
        :param success_row: success data
        :param taxon_id: id of the added taxonomy
        """
        success_row['taxon_id'] = 'http://{d}/admin/bims/taxonomy/{id}'.format(
            d=self.domain,
            id=taxon_id
        )
        self.success_list.append(success_row)

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

    def validate_parents(self, taxon, row):
        """
        Validating parent data from taxon,
        cross-check between parents of the database and parents of CSV.
        If the parent has a different value, update to the correct parent.
        :param taxon: Taxonomy object
        :param row: csv row data
        """
        parent = taxon.parent
        max_try = 15
        current_try = 1
        while parent and current_try < max_try:
            parent_rank = self.parent_rank(taxon.rank)
            if 'SUB' in parent_rank:
                parent_rank = self.parent_rank(parent_rank)
            try:
                csv_data = self.row_value(row, parent_rank.capitalize())
                if parent_rank.capitalize() == SPECIES:
                    csv_data = self.row_value(row, GENUS) + ' ' + csv_data
            except KeyError:
                parent = parent.parent
                continue
            while not csv_data and current_try < max_try:
                parent_rank = self.parent_rank(parent_rank)
                csv_data = self.row_value(row, parent_rank.capitalize())
                current_try += 1
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
            if taxon.rank.upper() != 'KINGDOM' and not parent:
                parent = self.get_parent(
                    row, current_rank=taxon.rank.capitalize()
                )
                if parent:
                    taxon.parent = parent
                    taxon.save()
            current_try += 1
        print('Parents has been validated')

    def get_taxonomy(self, taxon_name, scientific_name, rank):
        """
        Get taxonomy from database and gbif
        :param taxon_name: name of the taxon
        :param scientific_name: scientific name of the taxon
        :param rank: rank of the taxon
        :return: taxonomy object
        """
        taxon_data = Taxonomy.objects.filter(
            canonical_name__iexact=taxon_name,
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
                    parent.gbif_key = None
                    parent.gbif_data = {}
                    parent.save()
            else:
                parent, _ = Taxonomy.objects.get_or_create(
                    canonical_name=taxon_name,
                    scientific_name=scientific_name,
                    legacy_canonical_name=taxon_name,
                    rank=rank.upper()
                )
        else:
            parent = taxon_data[0]
        return parent

    def get_parent(self, row, current_rank=GENUS):
        taxon_name = self.row_value(row, current_rank)
        if not taxon_name:
            return None
        if current_rank == SPECIES:
            taxon_name = self.row_value(row, GENUS) + ' ' + taxon_name
        taxon = self.get_taxonomy(
            taxon_name,
            taxon_name,
            current_rank.upper()
        )
        if (
                not taxon.gbif_key or
                not taxon.parent or taxon.parent.rank != 'KINGDOM'):
            ranks = copy.copy(TAXON_RANKS)
            try:
                ranks = ranks[:ranks.index(current_rank)]
            except ValueError as e:
                print(current_rank)
                return
            if len(ranks) > 0:
                parent = self.get_parent(row, ranks[len(ranks)-1])
                if parent:
                    taxon.parent = parent
                    taxon.save()
        return taxon

    @staticmethod
    def row_value(row, key):
        """
        Get row value by key
        :param row: row data
        :param key: key
        :return: row value
        """
        row_value = ''
        try:
            row_value = row[key]
            row_value = row_value.replace('\xa0', ' ')
            row_value = row_value.replace('\xc2', '')
            row_value = row_value.replace('\\xa0', '')
            row_value = row_value.strip()
            row_value = re.sub(' +', ' ', row_value)
        except KeyError:
            pass
        return row_value

    def species_csv_dict_reader(self, csv_dict):
        """
        Read and process species from csv file
        :param csv_dict: csv data as dictionaries
        """
        index = 1
        for row in csv_dict:
            logger.debug(row)
            self.taxa_upload_session.progress = '{index}/{total}'.format(
                index=index,
                total=self.total_rows
            )
            self.taxa_upload_session.save()
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
            rank = self.row_value(row, 'Taxon Rank')
            if not rank:
                rank = self.row_value(row, 'Taxon rank')
            if not rank:
                if self.row_value(row, SUBSPECIES):
                    rank = SUBSPECIES
                elif self.row_value(row, SPECIES):
                    rank = SPECIES
                elif self.row_value(row, GENUS):
                    rank = GENUS
                elif self.row_value(row, SUBFAMILY):
                    rank = SUBFAMILY
                elif self.row_value(row, FAMILY):
                    rank = FAMILY
                elif self.row_value(row, ORDER):
                    rank = ORDER
                elif self.row_value(row, CLASS):
                    rank = CLASS
                elif self.row_value(row, PHYLUM):
                    rank = PHYLUM
                else:
                    self.error_file(
                        error_row=row,
                        error_message='Missing taxon rank'
                    )
                    continue
            taxa = Taxonomy.objects.filter(
                canonical_name__iexact=taxon_name,
                rank=rank.upper()
            )
            try:
                taxonomy = None
                if taxa.exists():
                    taxonomy = taxa[0]
                    logger.debug('{} already in the system'.format(
                        taxon_name
                    ))
                if not taxonomy:
                    # Fetch from gbif
                    taxonomy = fetch_all_species_from_gbif(
                        species=taxon_name,
                        taxonomic_rank=rank,
                        should_get_children=False,
                        fetch_vernacular_names=False,
                        use_name_lookup=True
                    )
                else:
                    # Try again with lookup
                    logger.debug('Use different method')
                    taxonomy = fetch_all_species_from_gbif(
                        species=taxon_name,
                        taxonomic_rank=rank,
                        should_get_children=False,
                        fetch_vernacular_names=False,
                        use_name_lookup=False
                    )

                # Validate data
                if taxonomy:
                    if (taxon_name not in taxonomy.scientific_name and
                            taxon_name.lower().strip() !=
                            taxonomy.canonical_name.lower().strip() and
                            taxon_name.lower() not in
                            taxonomy.legacy_canonical_name.lower()
                    ):
                        taxonomy = None
                    else:
                        if not taxonomy.parent:
                            taxonomy.parent = self.get_parent(row, rank)

                # Data from GBIF couldn't be found, so add it manually
                if not taxonomy:
                    parent = self.get_parent(row, rank)
                    if not parent:
                        self.error_file(
                            error_row=row,
                            error_message=(
                                'Data not found from gbif for this taxon and '
                                'its parents'
                            )
                        )
                        continue
                    else:
                        # Taxonomy not found, create one
                        taxonomy, _ = Taxonomy.objects.get_or_create(
                            scientific_name=scientific_name,
                            canonical_name=taxon_name,
                            rank=TaxonomicRank[rank.upper()].name,
                            parent=parent
                        )

                # -- Finish
                if taxonomy:
                    # Merge taxon with same canonical name
                    legacy_canonical_name = taxonomy.legacy_canonical_name
                    legacy_canonical_name = (
                        legacy_canonical_name.replace('\\xa0', '')
                    )
                    if FORMER_SPECIES_NAME in row:
                        former_species_name = self.row_value(
                            row, FORMER_SPECIES_NAME)
                        if len(former_species_name) > 500:
                            former_species_name = former_species_name[:500]
                        if former_species_name not in legacy_canonical_name:
                            legacy_canonical_name += ';' + former_species_name
                    taxonomy.legacy_canonical_name = (
                        legacy_canonical_name[:700]
                    )
                    # -- Import date
                    taxonomy.import_date = (
                        self.taxa_upload_session.uploaded_at.date()
                    )
                    self.success_file(
                        row,
                        taxonomy.id
                    )
                    # -- Validate parents
                    self.validate_parents(
                        taxon=taxonomy,
                        row=row
                    )
                    if taxonomy.canonical_name != taxon_name:
                        taxonomy.canonical_name = taxon_name
                        taxonomy.save()

            except Exception as e:  # noqa
                self.error_file(
                    error_row=row,
                    error_message=str(e)
                )

        headers = csv_dict.fieldnames
        file_name = self.taxa_upload_session.process_file.name.replace('taxa-file/', '')
        file_path = self.taxa_upload_session.process_file.path.replace(file_name, '')

        # Create error file
        # TODO : Done it simultaneously with file processing
        if self.error_list:
            error_headers = copy.deepcopy(headers)
            if 'error_message' not in error_headers:
                error_headers.append('error_message')
            error_file_path = '{path}error_{name}'.format(
                path=file_path,
                name=file_name
            )
            with open(error_file_path, mode='w') as csv_file:
                writer = csv.writer(
                    csv_file, delimiter=',', quotechar='"',
                    quoting=csv.QUOTE_MINIMAL)
                writer.writerow(error_headers)
                for data in self.error_list:
                    data_list = []
                    for key in error_headers:
                        try:
                            data_list.append(data[key])
                        except KeyError:
                            continue
                    writer.writerow(data_list)
            self.taxa_upload_session.error_file.name = (
                'taxa-file/error_{}'.format(
                    file_name
            ))

        # Create success file
        # TODO : Done it simultaneously with file processing
        if self.success_list:
            success_headers = copy.deepcopy(headers)
            if 'taxon_id' not in success_headers:
                success_headers.append('taxon_id')
            success_file_path = '{path}success_{name}'.format(
                path=file_path,
                name=file_name
            )
            with open(success_file_path, mode='w') as csv_file:
                writer = csv.writer(
                    csv_file, delimiter=',', quotechar='"',
                    quoting=csv.QUOTE_MINIMAL)
                writer.writerow(success_headers)
                for data in self.success_list:
                    data_list = []
                    for key in success_headers:
                        try:
                            data_list.append(data[key])
                        except KeyError:
                            continue
                    writer.writerow(data_list)
            self.taxa_upload_session.success_file.name = (
                'taxa-file/success_{}'.format(
                    file_name
            ))

        self.taxa_upload_session.processed = True
        self.taxa_upload_session.progress = 'Finished'
        self.taxa_upload_session.save()
