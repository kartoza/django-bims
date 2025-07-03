import copy
import json
import logging
import re

import requests
from django.db import transaction

from bims.api_views.taxon_update import create_taxon_proposal
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
    ORIGIN_CATEGORIES, TaxonTag, SourceReference,
    SourceReferenceBibliography,
    Invasion
)
from bims.templatetags import is_fada_site
from bims.utils.fetch_gbif import (
    fetch_all_species_from_gbif, fetch_gbif_vernacular_names
)
from bims.scripts.data_upload import DataCSVUpload
from td_biblio.exceptions import DOILoaderError
from td_biblio.models import Entry
from td_biblio.utils.loaders import DOILoader

from preferences import preferences

logger = logging.getLogger('bims')


class TaxaProcessor(object):

    all_keys = {}

    def add_taxon_to_taxon_group(self, taxonomy: Taxonomy, taxon_group: TaxonGroup, validated = True):
        """
        Add or update the relationship between a taxonomy and a taxon group,
        ensuring the 'is_validated' field is properly set in both the
        intermediate table (TaxonGroupTaxonomy) and on the Taxonomy object.
        """
        taxon_group.taxonomies.add(
            taxonomy,
            through_defaults={
                'is_validated': validated
            }
        )
        if not validated:
            taxon_group.taxonomies.through.objects.filter(
                taxongroup=taxon_group,
                taxonomy=taxonomy
            ).update(is_validated=False)

            create_taxon_proposal(taxonomy, taxon_group)

    def add_taxon_to_taxon_group_unvalidated(self, taxonomy, taxon_group):
        """
        A helper function that calls `add_taxon_to_taxon_group` with
        validated=True
        """
        self.add_taxon_to_taxon_group(taxonomy, taxon_group, validated=True)

    def handle_error(self, row, message):
        pass

    def finish_processing_row(self, row, taxonomy):
        pass

    def rank_name(self, taxon: Taxonomy):
        if taxon.rank:
            return taxon.rank.upper()
        return ''
    
    def get_row_value(self, row, key):
        return DataCSVUpload.row_value(row, key, self.all_keys)

    def endemism(self, row):
        """Processing endemism data"""
        endemism_value = self.get_row_value(row, ENDEMISM)
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
            cons_status = self.get_row_value(
                row, CONSERVATION_STATUS)
            if not cons_status:
                cons_status = self.get_row_value(
                    row, CONSERVATION_STATUS_GLOBAL)
                if not cons_status:
                    return None
        else:
            cons_status = self.get_row_value(
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
        source_reference_value = self.get_row_value(row, REFERENCES)
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
        """Extracts and processes common names of species from a given row."""

        common_name_value = self.get_row_value(row, COMMON_NAME)
        if not common_name_value:
            common_name_value = self.get_row_value(row, VERNACULAR_NAME)
            vernacular_lang = self.get_row_value(row, VERNACULAR_NAME_LANG)
        else:
            vernacular_lang = 'eng'

        if not common_name_value:
            return None

        vernacular_names = []

        # Split the common name string into individual names based on ';' or ',' as delimiters
        if ';' in common_name_value:
            common_names = common_name_value.split(';')
        else:
            common_names = common_name_value.split(',')
        for common_name in common_names:
            common_name = common_name.strip()

            # Match common names with an optional language code in parentheses
            # Example matches:
            # "Elephant" -> name: "Elephant", language: None (will use default english)
            # "Lion (eng)" -> name: "Lion", language: "eng"
            # "Tigre (spa)" -> name: "Tigre", language: "spa"
            # "Panda(chi)" -> name: "Panda", language: "chi" (handles no space before parentheses)
            match = re.match(r'^(.*?)(?: *\((\w+)\))?$', common_name)
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
        """
        Processes the origin information for a given row. Checks the origin and invasion
        status and returns the appropriate category and invasion instance if applicable.

        Args:
            row (dict): A dictionary representing a row of data from a CSV upload.

        Returns:
            tuple: A tuple containing the origin category (str) and an Invasion instance (or None).
        """
        origin_value = self.get_row_value(row, ORIGIN)
        invasion_category = self.get_row_value(row, INVASION)
        invasion_instance = None

        # Handle invasion category if provided
        if invasion_category:
            invasion_instance, _ = Invasion.objects.get_or_create(category=invasion_category)

        # If origin value is not provided, return default values
        if not origin_value:
            return '', invasion_instance

        # Check if origin indicates an invasive status without an explicit invasion category
        if 'invasive' in origin_value.lower() and not invasion_category:
            invasion_instance, _ = Invasion.objects.get_or_create(category=origin_value)
            return ORIGIN_CATEGORIES['non-native'], invasion_instance

        # Return the origin category if it exists in the predefined categories
        if origin_value.lower() not in ORIGIN_CATEGORIES:
            return '', invasion_instance

        return ORIGIN_CATEGORIES[origin_value.lower()], invasion_instance

    def validate_parents(self, taxon, row):
        """
        Validates and updates the parent hierarchy of a taxon based on CSV data.
        This function now includes sub-ranks like SUBFAMILY.
        :param taxon: Taxonomy object
        :param row: CSV row data
        """
        if not taxon:
            return False, 'Missing taxon'

        max_try = 15
        current_try = 1
        taxon_rank = taxon.rank.upper()

        if taxon_rank not in RANK_INDEX:
            return False, f"Rank '{taxon_rank}' not recognized in the hierarchy."

        # Start from the current taxon's rank and move up the hierarchy
        rank_index = RANK_INDEX[taxon_rank]

        while current_try <= max_try and rank_index > 0:
            parent_rank_name = RANK_HIERARCHY[rank_index - 1]
            current_try += 1

            if not taxon:
                return False, "Parent not found"

            # Try to get the parent name from the CSV data
            csv_parent_name = self.get_row_value(row, RANK_TITLE.get(
                parent_rank_name.upper(), parent_rank_name.capitalize()))

            # Handle species special case where genus might be part of the species name
            if parent_rank_name == 'SPECIES':
                genus_name = self.get_row_value(row, 'Genus')
                if genus_name and genus_name not in csv_parent_name:
                    csv_parent_name = f"{genus_name} {csv_parent_name}"

            # ----------------------------------------------------------------
            # If the row itself gives us nothing for this higher rank
            #      just climb another step and keep looking.
            # ----------------------------------------------------------------
            if not csv_parent_name:
                rank_index -= 1
                continue

            current_parent = taxon.parent

            # ----------------------------------------------------------------
            # Parent already exists – verify name/rank.
            # ----------------------------------------------------------------
            if current_parent:
                if (current_parent.canonical_name.lower() != csv_parent_name.lower() or
                        current_parent.rank.upper() != parent_rank_name):
                    # Mismatch  →  fetch / create the right parent
                    correct_parent = self.get_parent(
                        row,
                        current_rank=RANK_TITLE.get(
                            parent_rank_name.upper(),
                            parent_rank_name
                        )
                    )
                    if correct_parent:
                        taxon.parent = correct_parent
                        taxon.save()
                        taxon = correct_parent  # climb one level
                    else:
                        # Couldn’t resolve parent → abort gracefully
                        logger.warning(
                            "Cannot find/create parent '%s' (%s) for '%s'",
                            csv_parent_name, parent_rank_name, taxon.canonical_name
                        )
                        break
                else:
                    # Parent matches → move up one level
                    taxon = current_parent

            # ----------------------------------------------------------------
            # No parent saved yet – try to build one.
            # ----------------------------------------------------------------
            else:
                correct_parent = self.get_parent(row, parent_rank_name)
                if correct_parent:
                    taxon.parent = correct_parent
                    taxon.save()
                    taxon = correct_parent  # climb one level
                else:
                    logger.warning(
                        "Cannot find/create parent '%s' (%s) for '%s'",
                        csv_parent_name, parent_rank_name, taxon.canonical_name
                    )
                    break

            # prepare for next loop step
            rank_index -= 1

        # -------------------------------------------------------------------- #
        logger.debug("Parent validation finished for '%s'.", taxon.canonical_name
            if taxon else "unknown taxon")

        return True, ''

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
            taxon = fetch_all_species_from_gbif(
                species=taxon_name,
                taxonomic_rank=rank,
                fetch_children=False,
                fetch_vernacular_names=False
            )
            if taxon:
                if taxon_name.lower() not in taxon.scientific_name.lower():
                    taxon.scientific_name = scientific_name
                    taxon.legacy_canonical_name = taxon_name
                    taxon.canonical_name = taxon_name
                    taxon.gbif_key = None
                    taxon.gbif_data = {}
                    taxon.save()
            else:
                taxon, _ = Taxonomy.objects.get_or_create(
                    canonical_name=taxon_name,
                    scientific_name=scientific_name,
                    legacy_canonical_name=taxon_name,
                    rank=rank.upper()
                )
        else:
            taxon = taxon_data.first()
        return taxon

    def get_parent(self, row, current_rank=GENUS):
        # Retrieve the taxon name based on the current rank from the row data
        taxon_name = self.get_row_value(row, current_rank)
        if not taxon_name:
            return None

        # Handle concatenation for SPECIES rank
        if current_rank == SPECIES:
            genus_name = self.get_row_value(row, GENUS)
            if genus_name not in taxon_name:
                taxon_name = genus_name + ' ' + taxon_name

        # Handle concatenation for VARIETY rank
        if current_rank == VARIETY:
            genus_name = self.get_row_value(row, GENUS)
            species_name = self.get_row_value(row, SPECIES)
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
        if not self.all_keys:
            for key in row.keys():
                self.all_keys[key.upper()] = key

        taxonomic_status = self.get_row_value(row, TAXONOMIC_STATUS)
        taxon_name = self.get_row_value(row, TAXON)
        accepted_taxon = None

        # Get rank
        rank = self.get_row_value(row, TAXON_RANK)
        rank = RANK_TITLE.get(rank.upper(), rank.capitalize())
        if rank.startswith('Sub'):
            rank = 'Sub' + rank[len('sub'):].capitalize()

        if not rank:
            rank = self.get_row_value(row, 'Taxon rank')
        if not rank:
            self.handle_error(
                row=row,
                message='Missing taxon rank'
            )
            return

        if not taxon_name:
            taxon_name = self.get_row_value(
                row,
                RANK_TITLE.get(rank.upper(), rank.capitalize()))

        if 'species' in rank.lower():
            genus_name = self.get_row_value(row, GENUS).strip()
            species_name = self.get_row_value(row, SPECIES).strip()
            taxonomic_status = self.get_row_value(row, TAXONOMIC_STATUS).strip()
            if genus_name not in species_name and species_name and not species_name[0].isupper():
                taxon_name = genus_name + ' ' + species_name.strip()

        if rank == SUBSPECIES:
            sub_species_name = self.get_row_value(row, SUBSPECIES).strip()
            if taxon_name not in sub_species_name and sub_species_name and not sub_species_name[0].isupper():
                taxon_name = taxon_name + ' ' + sub_species_name

        try:
            on_gbif = (
                self.get_row_value(row, ON_GBIF).strip() and
                self.get_row_value(row, ON_GBIF) in (
                    'Yes', 'yes', 'True', 'true')
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

        if 'synonym' in taxonomic_status.lower().lower().strip():
            accepted_taxon_val = self.get_row_value(
                row, ACCEPTED_TAXON
            )
            if accepted_taxon_val:
                accepted_taxon = Taxonomy.objects.filter(
                    canonical_name__iexact=accepted_taxon_val
                ).first()

        authors = self.get_row_value(row, AUTHORS)

        if SCIENTIFIC_NAME in row:
            scientific_name = (self.get_row_value(row, SCIENTIFIC_NAME)
                               if self.get_row_value(row, SCIENTIFIC_NAME)
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

            gbif_key = None
            if on_gbif:
                gbif_link = self.get_row_value(row, GBIF_LINK)
                if not gbif_link:
                    gbif_link = self.get_row_value(row, GBIF_URL)
                gbif_key = (
                    gbif_link.split('/')[len(gbif_link.split('/')) - 1]
                )

            if not taxonomy:
                # Fetch from gbif
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
                    not self.get_row_value(row, parent_name) and parent_name != KINGDOM and current_try < max_try
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
                    former_species_name = self.get_row_value(
                        row, FORMER_SPECIES_NAME)
                    if len(former_species_name) > 500:
                        former_species_name = former_species_name[:500]
                    if former_species_name not in legacy_canonical_name:
                        legacy_canonical_name += ';' + former_species_name
                taxonomy.legacy_canonical_name = (
                    legacy_canonical_name[:700]
                )
                # -- Validate parents
                validated, message = self.validate_parents(
                    taxon=taxonomy,
                    row=row
                )

                if not validated:
                    self.handle_error(
                        row=row,
                        message=message
                    )
                    return

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

                fada_id = self.get_row_value(row, FADA_ID)
                # -- FADA ID
                if fada_id:
                    try:
                        integer_part = fada_id.split('.', 1)[0]
                        taxonomy.fada_id = int(integer_part)
                    except ValueError:
                        pass

                if gbif_key:
                    taxonomy.gbif_key = gbif_key

                # -- Tags | Biographic distribution tags

                # Clear tags
                taxonomy.tags.clear()
                taxonomy.biographic_distributions.clear()

                # Adding tags
                # Check Y Values
                for key in row:
                    row_value = self.get_row_value(row, key)
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

                taxonomy.save()

                # -- Add to taxon group
                self.add_taxon_to_taxon_group_unvalidated(taxonomy, taxon_group)

                self.finish_processing_row(row, taxonomy)
        except Exception as e:  # noqa
            self.handle_error(row, str(e))


class TaxaCSVUpload(DataCSVUpload, TaxaProcessor):
    model_name = 'taxonomy'

    def add_taxon_to_taxon_group_unvalidated(self, taxonomy, taxon_group):
        """
        A helper function that calls `add_taxon_to_taxon_group` with
        validated=False
        """
        auto_validate = preferences.SiteSetting.auto_validate_taxa_on_upload
        self.add_taxon_to_taxon_group(taxonomy, taxon_group, validated=auto_validate)

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
