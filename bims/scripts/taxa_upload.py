import copy
import json
import logging
import re

import requests
from django.db import transaction

from bims.models.taxon_group import TaxonGroup
from bims.scripts.collections_upload_source_reference import get_or_create_data_from_model

from bims.scripts.species_keys import *  # noqa
from bims.enums import TaxonomicRank
from bims.models import (
    Taxonomy,
    Endemism,
    IUCNStatus,
    IUCN_CATEGORIES,
    VernacularName,
    ORIGIN_CATEGORIES, TaxonTag, SourceReference, SourceReferenceBibliography,
    Invasion
)
from bims.templatetags import is_fada_site
from bims.utils.fetch_gbif import (
    fetch_all_species_from_gbif, fetch_gbif_vernacular_names
)
from bims.scripts.data_upload import DataCSVUpload
from bims.utils.gbif import get_vernacular_names
from td_biblio.exceptions import DOILoaderError
from td_biblio.models import Entry
from td_biblio.utils.loaders import DOILoader

logger = logging.getLogger('bims')


class TaxaProcessor(object):

    def handle_error(self, row, message):
        pass

    def finish_processing_row(self, row, taxonomy):
        pass

    def rank_name(self, taxon: Taxonomy):
        if taxon.rank:
            return taxon.rank.upper()
        return ''

    def endemism(self, row):
        """Processing endemism data"""
        endemism_value = DataCSVUpload.row_value(row, ENDEMISM)
        if not endemism_value:
            return None
        try:
            endemism_obj, _ = Endemism.objects.get_or_create(
                name=endemism_value
            )
        except Endemism.MultipleObjectsReturned:
            endemism_obj = Endemism.objects.filter(
                name=endemism_value
            )[0]
        return endemism_obj

    def conservation_status(self, row, global_cons = False):
        """Processing conservation status"""
        national = False
        if global_cons:
            cons_status = DataCSVUpload.row_value(
                row, CONSERVATION_STATUS)
            if not cons_status:
                cons_status = DataCSVUpload.row_value(
                    row, CONSERVATION_STATUS_GLOBAL)
                if not cons_status:
                    return None
        else:
            cons_status = DataCSVUpload.row_value(
                row, CONSERVATION_STATUS_NATIONAL)
            national = True
        if cons_status:
            try:
                iucn_status, _ = IUCNStatus.objects.get_or_create(
                    category=IUCN_CATEGORIES[cons_status.lower()],
                    national=national
                )
            except IUCNStatus.MultipleObjectsReturned:
                iucn_status = IUCNStatus.objects.filter(
                    category=IUCN_CATEGORIES[cons_status.lower()],
                    national=national
                ).first()
            return iucn_status
        else:
            return None

    def source_reference(self, row):
        source_reference_value = DataCSVUpload.row_value(row, REFERENCES)
        if not source_reference_value:
            return '', None

        source_reference = None

        # Check if the reference is DOI
        doi_pattern = r'^10.\d{4,9}/[-._;()/:A-Z0-9]+$'
        is_doi = re.match(doi_pattern, source_reference_value, re.IGNORECASE) is not None
        if is_doi:
            entry = get_or_create_data_from_model(
                model=Entry,
                fields={
                    'doi': source_reference_value
                },
                create=False
            )
            if not entry:
                doi_loader = DOILoader()
                try:
                    doi_loader.load_records(DOIs=[source_reference_value])
                    doi_loader.save_records()
                    entry_fields = {
                        'doi__iexact': source_reference_value
                    }
                    entry = get_or_create_data_from_model(
                        Entry,
                        entry_fields,
                        create=False
                    )
                except (
                        DOILoaderError,
                        requests.exceptions.HTTPError) as e:
                    print(e)
                finally:
                    if not entry:
                        return 'Error Fetching DOI : {doi}', None
            if entry and not source_reference:
                SourceReference.create_source_reference(
                    category='bibliography',
                    source_id=entry.id,
                    note=None
                )
                try:
                    source_reference, _ = (
                        SourceReferenceBibliography.objects.get_or_create(
                            source=entry
                        )
                    )
                except SourceReferenceBibliography.MultipleObjectsReturned:
                    source_reference = SourceReferenceBibliography.objects.filter(
                        source=entry
                    ).first()
        else:
            # Create unpublished
            source_reference = (
                SourceReference.create_source_reference(
                    category=None,
                    source_id=None,
                    note=source_reference_value
                )
            )
        return '', source_reference

    def common_name(self, row):
        """Common name of species"""
        common_name_value = DataCSVUpload.row_value(row, COMMON_NAME)
        if not common_name_value:
            common_name_value = DataCSVUpload.row_value(row, VERNACULAR_NAME)
            vernacular_lang = DataCSVUpload.row_value(row, VERNACULAR_NAME_LANG)
        else:
            vernacular_lang = 'eng'

        if not common_name_value:
            return None

        vernacular_names = []
        common_names = common_name_value.split(',')
        for common_name in common_names:
            common_name = common_name.strip()
            match = re.match(r'^(.*?)(?: \((\w+)\))?$', common_name)
            if match:
                name = match.group(1)
                language = match.group(2) if match.group(2) else vernacular_lang
                try:
                    vernacular_name, _ = VernacularName.objects.get_or_create(
                        name=name,
                        language=language,
                        is_upload=True
                    )
                except VernacularName.MultipleObjectsReturned:
                    vernacular_name = VernacularName.objects.filter(
                        name=name,
                        language=language,
                        is_upload=True
                    )[0]
                vernacular_names.append(vernacular_name)
        return vernacular_names

    def origin(self, row):
        """Processing origin"""
        origin_value = DataCSVUpload.row_value(row, ORIGIN)
        if not origin_value:
            return '', None
        if 'invasive' in origin_value.lower():
            invasive, _ = Invasion.objects.get_or_create(
                category=origin_value
            )
            return ORIGIN_CATEGORIES['non-native'], invasive
        if origin_value.lower() not in ORIGIN_CATEGORIES:
            return '', None
        return ORIGIN_CATEGORIES[origin_value.lower()], None

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
            taxon_parent_rank = parent_rank(taxon.rank)
            try:
                csv_data = DataCSVUpload.row_value(
                    row, taxon_parent_rank.capitalize())
                if taxon_parent_rank == SPECIES:
                    genus = DataCSVUpload.row_value(
                        row, GENUS)
                    if genus not in csv_data:
                        csv_data = DataCSVUpload.row_value(
                            row, GENUS) + ' ' + csv_data
            except KeyError:
                parent = parent.parent
                continue
            while not csv_data and current_try < max_try:
                taxon_parent_rank = parent_rank(taxon_parent_rank)
                csv_data = DataCSVUpload.row_value(
                    row, taxon_parent_rank)
                current_try += 1
            if (
                    csv_data not in parent.canonical_name and
                    csv_data not in parent.legacy_canonical_name or
                    self.rank_name(parent) != taxon_parent_rank.upper()
            ):
                print('Different parent for {}'.format(str(taxon)))
                taxon_parent = self.get_parent(
                    row,
                    current_rank=PARENT_RANKS.get(taxon_parent_rank.upper(), '')
                )
                print('Updated to {}'.format(str(taxon_parent)))
                taxon.parent = taxon_parent
                taxon.save()
            taxon = parent
            parent = parent.parent
            if self.rank_name(taxon) != 'KINGDOM' and not parent:
                parent = self.get_parent(
                    row, current_rank=PARENT_RANKS.get(taxon.rank.upper(), '')
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
                fetch_children=False,
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
        # Retrieve the taxon name based on the current rank from the row data
        taxon_name = DataCSVUpload.row_value(row, current_rank)
        if not taxon_name:
            return None

        # Handle concatenation for SPECIES rank
        if current_rank == SPECIES:
            genus_name = DataCSVUpload.row_value(row, GENUS)
            if genus_name not in taxon_name:
                taxon_name = genus_name + ' ' + taxon_name

        # Handle concatenation for VARIETY rank
        if current_rank == VARIETY:
            genus_name = DataCSVUpload.row_value(row, GENUS)
            species_name = DataCSVUpload.row_value(row, SPECIES)
            if species_name not in taxon_name:
                taxon_name = species_name + ' ' + taxon_name
            if genus_name not in taxon_name:
                taxon_name = genus_name + ' ' + taxon_name

        # Fetch the taxon using the constructed taxon name and current rank
        taxon = self.get_taxonomy(
            taxon_name,
            taxon_name,
            current_rank.upper()
        )

        # If the taxon already has a parent, return it
        if taxon.parent and taxon.parent.rank:
            return taxon

        # Loop to find and assign the parent taxon until the conditions are met
        while not taxon.gbif_key or (taxon.parent and taxon.parent.rank != 'KINGDOM'):
            # Exit the loop if the current taxon rank is 'KINGDOM'
            if taxon.rank == 'KINGDOM':
                break

            # Determine the parent rank name
            parent_rank_name = parent_rank(current_rank)
            if not parent_rank_name:
                break

            # Recursively get the parent taxon
            parent = self.get_parent(row, parent_rank_name)
            if parent:
                taxon.parent = parent
                taxon.save()
                break

            # Update the current rank for the next iteration
            current_rank = parent_rank_name

        return taxon

    def synonym_key(self, field_key):
        return f'{SYNONYM} {field_key}'

    def process_data(self, row, taxon_group: TaxonGroup):
        """Processing row of the csv files"""

        taxonomic_status = DataCSVUpload.row_value(row, TAXONOMIC_STATUS)
        taxon_name = DataCSVUpload.row_value(row, TAXON)
        accepted_taxon = None

        # Get rank
        rank = DataCSVUpload.row_value(row, TAXON_RANK)
        rank = rank.capitalize()
        if rank.startswith('Sub'):
            rank = 'Sub' + rank[len('sub'):].capitalize()

        if not rank:
            rank = DataCSVUpload.row_value(row, 'Taxon rank')
        if not rank:
            self.handle_error(
                row=row,
                message='Missing taxon rank'
            )
            return

        if not taxon_name:
            taxon_name = DataCSVUpload.row_value(row, rank.capitalize())

        if rank == SPECIES:
            genus_name = DataCSVUpload.row_value(row, GENUS).strip()
            if genus_name not in taxon_name:
                taxon_name = genus_name + ' ' + taxon_name.strip()

        try:
            on_gbif = (
                DataCSVUpload.row_value(row, ON_GBIF).strip() and
                DataCSVUpload.row_value(row, ON_GBIF) != 'No'
            )
        except Exception:  # noqa
            if is_fada_site():
                on_gbif = False
            else:
                on_gbif = True

        if not taxon_name:
            self.handle_error(
                row=row,
                message='Missing Taxon value'
            )
            return

        if 'synonym' in taxonomic_status.lower().strip():
            accepted_taxon_val = DataCSVUpload.row_value(
                row, ACCEPTED_TAXON
            )
            accepted_taxon_err = ''
            if not accepted_taxon_val:
                accepted_taxon_err = 'Synonym missing accepted taxon'
            else:
                accepted_taxon = Taxonomy.objects.filter(
                    canonical_name__iexact=accepted_taxon_val
                ).first()
                if not accepted_taxon:
                    accepted_taxon_err = (
                        'The accepted taxon is not in the system yet'
                    )

            if accepted_taxon_err:
                self.handle_error(
                    row=row,
                    message=accepted_taxon_err
                )
                return

        authors = DataCSVUpload.row_value(row, AUTHORS)

        if SCIENTIFIC_NAME in row:
            scientific_name = (DataCSVUpload.row_value(row, SCIENTIFIC_NAME)
                               if DataCSVUpload.row_value(row, SCIENTIFIC_NAME)
                               else taxon_name)
        else:
            scientific_name = taxon_name
        scientific_name = scientific_name.strip()

        if authors not in scientific_name:
            scientific_name = f'{scientific_name} {authors}'

        # Check if parent and taxon has the same name
        parent = self.get_parent(row, parent_rank(rank))
        if parent and parent.canonical_name == taxon_name:
            self.handle_error(
                row=row,
                message='Parent cannot have the same name as the taxon'
            )
            return

        taxa = Taxonomy.objects.filter(
            canonical_name__iexact=taxon_name
        )
        try:
            taxonomy = None

            common_name = self.common_name(row)
            if not common_name:
                should_fetch_vernacular_names = True
            else:
                should_fetch_vernacular_names = False

            if taxa.exists():
                taxa_same_rank = taxa.filter(
                    rank=rank.upper()
                )
                if taxa_same_rank.exists():
                    taxonomy = taxa_same_rank.first()
                else:
                    taxonomy = taxa.first()

                if taxonomy.rank != rank.upper():
                    logger.debug('{} has different RANK'.format(
                        taxon_name
                    ))
                    taxonomy.rank = rank.upper()

                logger.debug('{} already in the system'.format(
                    taxon_name
                ))
            if not taxonomy:
                # Fetch from gbif
                if on_gbif:
                    gbif_link = DataCSVUpload.row_value(row, GBIF_LINK)
                    if not gbif_link:
                        gbif_link = DataCSVUpload.row_value(row, GBIF_URL)
                    gbif_key = (
                        gbif_link.split('/')[len(gbif_link.split('/')) - 1]
                    )
                    if gbif_key:
                        taxonomy = fetch_all_species_from_gbif(
                            gbif_key=gbif_key,
                            fetch_vernacular_names=should_fetch_vernacular_names
                        )
                if not taxonomy and on_gbif:
                    taxonomy = fetch_all_species_from_gbif(
                        species=taxon_name,
                        taxonomic_rank=rank,
                        fetch_children=False,
                        fetch_vernacular_names=should_fetch_vernacular_names,
                        use_name_lookup=True
                    )

            if not taxonomy and on_gbif:
                # Try again with lookup
                logger.debug('Use different method')
                taxonomy = fetch_all_species_from_gbif(
                    species=taxon_name,
                    taxonomic_rank=rank,
                    fetch_children=False,
                    fetch_vernacular_names=should_fetch_vernacular_names,
                    use_name_lookup=False
                )

            # Taxonomy found or created then validate it
            if taxonomy:
                if not taxonomy.parent and parent:
                    taxonomy.parent = parent

            # Data from GBIF couldn't be found, so add it manually
            if not taxonomy:
                max_try = 10
                current_try = 0
                parent_name = parent_rank(rank)
                while (
                    not DataCSVUpload.row_value(row, parent_name) and parent_name != KINGDOM and current_try < max_try
                ):
                    current_try += 1
                    parent_name = parent_rank(parent_name)

                parent = self.get_parent(row, parent_name)
                if not parent:
                    self.handle_error(
                        row=row,
                        message=(
                            'Data not found from gbif for this taxon and '
                            'its parents'
                        )
                    )
                    return
                else:
                    # Taxonomy not found, create one
                    taxonomy, _ = Taxonomy.objects.get_or_create(
                        scientific_name=scientific_name,
                        canonical_name=taxon_name,
                        rank=TaxonomicRank[rank.upper()].name,
                        parent=parent
                    )
                    if taxonomic_status:
                        taxonomy.taxonomic_status = (
                            taxonomic_status.upper()
                        )

            # -- Finish
            if taxonomy:
                # Merge taxon with same canonical name
                legacy_canonical_name = taxonomy.legacy_canonical_name
                legacy_canonical_name = (
                    legacy_canonical_name.replace('\\xa0', '')
                )
                if FORMER_SPECIES_NAME in row:
                    former_species_name = DataCSVUpload.row_value(
                        row, FORMER_SPECIES_NAME)
                    if len(former_species_name) > 500:
                        former_species_name = former_species_name[:500]
                    if former_species_name not in legacy_canonical_name:
                        legacy_canonical_name += ';' + former_species_name
                taxonomy.legacy_canonical_name = (
                    legacy_canonical_name[:700]
                )
                # -- Validate parents
                self.validate_parents(
                    taxon=taxonomy,
                    row=row
                )

                # -- Add to taxon group
                taxon_group.taxonomies.add(
                    taxonomy,
                    through_defaults={
                        'is_validated': True
                    }
                )

                # -- Endemism
                endemism = self.endemism(row)
                if endemism:
                    taxonomy.endemism = endemism

                # -- Conservation status global
                iucn_status = self.conservation_status(row, True)
                if iucn_status:
                    taxonomy.iucn_status = iucn_status

                # -- Conservation status national
                national_cons_status = self.conservation_status(row, False)
                if national_cons_status:
                    taxonomy.national_conservation_status = (
                        national_cons_status
                    )

                # -- References
                message, reference = self.source_reference(row)
                if message and not reference:
                    self.handle_error(
                        row=row,
                        message=message
                    )
                    return
                if reference:
                    taxonomy.source_reference = reference

                # -- Common name
                if common_name:
                    taxonomy.vernacular_names.clear()
                    for _common_name in common_name:
                        taxonomy.vernacular_names.add(_common_name)
                else:
                    if (
                        not taxonomy.vernacular_names.exists() and
                        taxonomy.gbif_key
                    ):
                        fetch_gbif_vernacular_names(taxonomy)

                # -- Origin
                origin_data, invasion = self.origin(row)
                if origin_data:
                    taxonomy.origin = origin_data

                if invasion:
                    taxonomy.invasion = invasion

                # -- Author(s)
                if authors:
                    taxonomy.author = authors

                # -- Tags | Biographic distribution tags
                # Check Y Values
                for key in row:
                    row_value = DataCSVUpload.row_value(row, key)
                    if row_value.upper() == 'Y' or row_value == '?':
                        # Remove (Y/N) or (y/n) from the key if present
                        tag_key = re.sub(r'\(y/n\)', '',
                                         key,
                                         flags=re.IGNORECASE).strip()
                        if key in BIOGRAPHIC_DISTRIBUTIONS:
                            if row_value == '?':
                                tag_key = f'{tag_key} (?)'
                            try:
                                taxon_tag, _ = TaxonTag.objects.get_or_create(
                                    name=tag_key,
                                    doubtful=row_value == '?'
                                )
                            except TaxonTag.MultipleObjectsReturned:
                                taxon_tag = TaxonTag.objects.filter(
                                    name=tag_key,
                                    doubtful=row_value == '?'
                                ).first()
                            taxonomy.biographic_distributions.add(taxon_tag)
                        elif row_value != '?':
                            taxonomy.tags.add(tag_key)

                # -- Additional data
                taxonomy.additional_data = json.dumps(row)

                if taxonomy.canonical_name != taxon_name:
                    taxonomy.canonical_name = taxon_name

                if taxonomic_status:
                    taxonomy.taxonomic_status = (
                        taxonomic_status.strip().upper()
                    )

                if accepted_taxon:
                    taxonomy.accepted_taxonomy = accepted_taxon

                taxonomy.validated = True

                taxonomy.save()
                self.finish_processing_row(row, taxonomy)
        except Exception as e:  # noqa
            self.handle_error(row, str(e))


class TaxaCSVUpload(DataCSVUpload, TaxaProcessor):
    model_name = 'taxonomy'

    def finish_processing_row(self, row, taxonomy):
        # -- Add to taxon group
        taxon_group = self.upload_session.module_group
        if not taxon_group.taxonomies.filter(
            id=taxonomy.id
        ).exists():
            taxon_group.taxonomies.add(taxonomy)

        # -- Add import date
        taxonomy.import_date = (
            self.upload_session.uploaded_at.date()
        )
        taxonomy.save()

        self.success_file(
            row,
            taxonomy.id
        )

    def handle_error(self, row, message):
        self.error_file(
            error_row=row,
            error_message=message
        )

    def process_row(self, row):
        taxon_group = self.upload_session.module_group
        with transaction.atomic():
            self.process_data(row, taxon_group)
