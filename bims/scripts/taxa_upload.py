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
    Invasion, SpeciesGroup,
    TaxonomyUpdateProposal
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

_TRUTHY = {'y', 'true', 't', '✓'}

def _as_truthy(val) -> bool:
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in _TRUTHY

def _norm_key_label(s: str) -> str:
    # Remove "(y/n)" and collapse whitespace
    return re.sub(r'\(y/n\)', '', str(s), flags=re.IGNORECASE).strip()

def _safe_upper(s):
    return str(s or '').upper()

def _safe_strip(s):
    return str(s or '').strip()


class TaxaProcessor(object):

    all_keys = {}

    def _get_or_create_vernacular_singleton(self, name: str, language: str | None):
        """
        Robustly fetch a single VernacularName without raising MultipleObjectsReturned.
        If multiples exist, return the earliest one. If none, create one.
        """
        name = re.sub(r'\s+', ' ', (name or '').strip())
        language = (language or '').strip() or None

        qs = VernacularName.objects.filter(
            name=name,
            language=language,
            is_upload=True
        ).order_by('id')

        obj = qs.first()
        if obj:
            return obj

        return VernacularName.objects.create(
            name=name,
            language=language,
            is_upload=True
        )

    def _update_taxon_and_proposal(self, taxonomy, proposal, use_proposal, new_taxon, field, value):
        # Apply on taxonomy for brand-new objects or when proposals are disabled.
        if new_taxon or not use_proposal:
            setattr(taxonomy, field, value)
        # Apply on proposal when proposals are enabled.
        if use_proposal and proposal is not None:
            setattr(proposal, field, value)

    def _compose_species_name(self, row) -> str:
        """
        Return a canonical binomial/trinomial.

        • If the species cell already starts with the genus, normalize capitalization.
        • Otherwise prepend the genus.
        • Always force epithets (everything after the genus) to lower-case.
        """
        genus = _safe_strip(self.get_row_value(row, GENUS))
        species = _safe_strip(self.get_row_value(row, SPECIES))

        if not species:
            species = _safe_strip(self.get_row_value(row, TAXON))

        if not genus or not species:
            return species or genus

        parts = species.split()
        epithets = ' '.join(p.lower() for p in parts[1:]) if len(parts) > 1 else ''
        # If species already includes genus (case-insensitive), normalize capitalization.
        if species.lower().startswith(genus.lower() + ' '):
            genus_cap = genus[:1].upper() + genus[1:].lower()
            rest = species.split(' ', 1)[1] if ' ' in species else ''
            rest_norm = ' '.join(w.lower() for w in rest.split())
            return f'{genus_cap} {rest_norm}'.strip()

        genus_cap = genus[:1].upper() + genus[1:].lower()
        species_lc = parts[0].lower()
        tail = f' {epithets}' if epithets else ''
        return f'{genus_cap} {species_lc}{tail}'.strip()

    def add_taxon_to_taxon_group(self, taxonomy: Taxonomy, taxon_group: TaxonGroup, validated: bool = True):
        """
        Add or update the relationship between a taxonomy and a taxon group,
        ensuring the 'is_validated' field is properly set in the through table.
        """
        taxon_group.taxonomies.add(
            taxonomy,
            through_defaults={'is_validated': validated}
        )
        if not validated:
            taxon_group.taxonomies.through.objects.filter(
                taxongroup=taxon_group,
                taxonomy=taxonomy
            ).update(is_validated=False)

    def add_taxon_to_taxon_group_unvalidated(self, taxonomy, taxon_group):
        """
        Helper for legacy callers. Note: this base implementation uses validated=True.
        TaxaCSVUpload overrides this to respect site preferences.
        """
        self.add_taxon_to_taxon_group(taxonomy, taxon_group, validated=True)

    def handle_error(self, row, message):
        pass

    def finish_processing_row(self, row, taxonomy):
        pass

    def rank_name(self, taxon: Taxonomy):
        return (taxon.rank or '').upper() if taxon and taxon.rank else ''

    def get_row_value(self, row, key):
        return DataCSVUpload.row_value(row, key, self.all_keys)

    def endemism(self, row):
        """Processing endemism data (case-insensitive, avoids dupes)."""
        endemism_value = _safe_strip(self.get_row_value(row, ENDEMISM))
        if not endemism_value:
            return None
        try:
            endemism_obj, _ = Endemism.objects.get_or_create(
                name__iexact=endemism_value,
                defaults={'name': endemism_value}
            )
        except Endemism.MultipleObjectsReturned:
            endemism_obj = Endemism.objects.filter(
                name__iexact=endemism_value
            ).order_by('id').first()
        return endemism_obj

    def conservation_status(self, row, global_cons: bool = False):
        """Processing conservation status with graceful fallbacks."""
        national = False
        if global_cons:
            cons_status = self.get_row_value(row, CONSERVATION_STATUS) or self.get_row_value(row, CONSERVATION_STATUS_GLOBAL)
            if not cons_status:
                return None
        else:
            cons_status = self.get_row_value(row, CONSERVATION_STATUS_NATIONAL)
            national = True

        if not cons_status:
            return None

        key = str(cons_status).strip().lower()
        category = IUCN_CATEGORIES.get(key)
        if not category:
            return None

        try:
            iucn_status, _ = IUCNStatus.objects.get_or_create(
                category=category,
                national=national
            )
        except IUCNStatus.MultipleObjectsReturned:
            iucn_status = IUCNStatus.objects.filter(
                category=category,
                national=national
            ).order_by('id').first()
        return iucn_status

    def source_reference(self, row):
        source_reference_value = _safe_strip(self.get_row_value(row, REFERENCES))
        if not source_reference_value:
            return '', None

        source_reference = None

        # DOI?
        doi_pattern = r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$'
        is_doi = re.match(doi_pattern, source_reference_value, re.IGNORECASE) is not None
        if is_doi:
            entry = get_or_create_data_from_model(
                model=Entry,
                fields={'doi': source_reference_value},
                create=False
            )
            if not entry:
                doi_loader = DOILoader()
                try:
                    doi_loader.load_records(DOIs=[source_reference_value])
                    doi_loader.save_records()
                    entry = get_or_create_data_from_model(
                        Entry,
                        {'doi__iexact': source_reference_value},
                        create=False
                    )
                except (DOILoaderError, requests.exceptions.HTTPError) as e:
                    logger.warning('DOI fetch failed for %s: %s', source_reference_value, e)
                finally:
                    if not entry:
                        return f'Error fetching DOI: {source_reference_value}', None

            if entry and not source_reference:
                SourceReference.create_source_reference(
                    category='bibliography',
                    source_id=entry.id,
                    note=None
                )
                try:
                    source_reference, _ = SourceReferenceBibliography.objects.get_or_create(source=entry)
                except SourceReferenceBibliography.MultipleObjectsReturned:
                    source_reference = SourceReferenceBibliography.objects.filter(source=entry).order_by('id').first()
        else:
            # Unpublished string note
            source_reference = SourceReference.create_source_reference(
                category=None,
                source_id=None,
                note=source_reference_value
            )
        return '', source_reference

    def common_name(self, row):
        """Extract and process common names of a species row; never raises on duplicates."""
        common_name_value = self.get_row_value(row, COMMON_NAME)
        vernacular_lang = None
        if not common_name_value:
            common_name_value = self.get_row_value(row, VERNACULAR_NAME)
            vernacular_lang = self.get_row_value(row, VERNACULAR_NAME_LANG)
        else:
            vernacular_lang = 'eng'

        if not common_name_value:
            return None

        vernacular_names = []
        raw_str = str(common_name_value)
        parts = raw_str.split(';') if ';' in raw_str else raw_str.split(',')
        for raw in parts:
            raw = raw.strip()
            if not raw:
                continue
            m = re.match(r'^(.*?)(?:\s*\(([\w-]+)\))?$', raw)
            if not m:
                continue

            name = re.sub(r'\s+', ' ', (m.group(1) or '').strip())
            language = (m.group(2) or vernacular_lang or '').strip() or None
            vn = self._get_or_create_vernacular_singleton(name=name, language=language)
            vernacular_names.append(vn)

        return vernacular_names or None

    def origin(self, row):
        """
        Parse origin + invasion status.
        Returns: (origin_category_str | '', invasion_instance | None)
        """
        origin_value = _safe_strip(self.get_row_value(row, ORIGIN))
        invasion_category = _safe_strip(self.get_row_value(row, INVASION))
        invasion_instance = None

        if invasion_category:
            invasion_instance, _ = Invasion.objects.get_or_create(category=invasion_category)

        if not origin_value:
            return '', invasion_instance

        if 'invasive' in origin_value.lower() and not invasion_category:
            invasion_instance, _ = Invasion.objects.get_or_create(category=origin_value)
            return ORIGIN_CATEGORIES.get('non-native', ''), invasion_instance

        key = origin_value.lower()
        if key not in ORIGIN_CATEGORIES:
            return '', invasion_instance

        return ORIGIN_CATEGORIES[key], invasion_instance

    def validate_parents(self, taxon, row):
        """
        Validate and (if needed) rebuild the parent chain using CSV hints.
        """
        if not taxon:
            return False, 'Missing taxon'

        if not taxon.rank or self.rank_name(taxon) not in RANK_INDEX:
            return False, f"Rank '{self.rank_name(taxon) or 'UNKNOWN'}' not recognized in the hierarchy."

        max_try = 15
        current_try = 0
        rank_index = RANK_INDEX[self.rank_name(taxon)]

        while current_try < max_try and rank_index > 0:
            current_try += 1
            parent_rank_name = RANK_HIERARCHY[rank_index - 1]
            csv_parent_name = self.get_row_value(row, RANK_TITLE.get(parent_rank_name.upper(), parent_rank_name.capitalize()))

            # When setting a SPECIES parent for a subspecific rank, ensure genus is included.
            if parent_rank_name == 'SPECIES' and csv_parent_name:
                genus_name = _safe_strip(self.get_row_value(row, 'Genus'))
                if genus_name and genus_name.lower() not in str(csv_parent_name).lower():
                    csv_parent_name = f'{genus_name} {csv_parent_name}'.strip()

            if not csv_parent_name:
                rank_index -= 1
                continue

            current_parent = taxon.parent

            if current_parent:
                # Mismatch -> fetch/create correct parent
                if current_parent.canonical_name.lower() != str(csv_parent_name).lower() or _safe_upper(current_parent.rank) != parent_rank_name:
                    correct_parent = self.get_parent(row, RANK_TITLE.get(parent_rank_name.upper(), parent_rank_name))
                    if correct_parent:
                        taxon.parent = correct_parent
                        taxon.save()
                        taxon = correct_parent
                    else:
                        logger.warning("Cannot resolve parent '%s' (%s) for '%s'", csv_parent_name, parent_rank_name, taxon.canonical_name)
                        break
                else:
                    taxon = current_parent
            else:
                correct_parent = self.get_parent(row, parent_rank_name)
                if correct_parent:
                    taxon.parent = correct_parent
                    taxon.save()
                    taxon = correct_parent
                else:
                    logger.warning("Cannot resolve parent '%s' (%s) for '%s'", csv_parent_name, parent_rank_name, taxon.canonical_name)
                    break

            rank_index -= 1

        logger.debug("Parent validation finished for '%s'.", taxon.canonical_name if taxon else 'unknown')
        return True, ''

    def get_taxonomy(self, taxon_name, scientific_name, rank):
        """
        Find or create a taxonomy by canonical name + rank, with GBIF fallback.
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
                if taxon_name.lower() not in (taxon.scientific_name or '').lower():
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
        taxon_name = self.get_row_value(row, current_rank)
        if not taxon_name:
            return None
        taxon_name = str(taxon_name).strip()

        # SPECIES: ensure Genus + epithet
        if current_rank == SPECIES:
            genus_name = _safe_strip(self.get_row_value(row, GENUS))
            if genus_name and genus_name.lower() not in taxon_name.lower():
                taxon_name = f'{genus_name} {taxon_name}'

        if current_rank == VARIETY:
            genus_name = _safe_strip(self.get_row_value(row, GENUS))
            species_name = _safe_strip(self.get_row_value(row, SPECIES))
            if species_name and species_name.lower() not in taxon_name.lower():
                taxon_name = f'{species_name} {taxon_name}'
            if genus_name and genus_name.lower() not in taxon_name.lower():
                taxon_name = f'{genus_name} {taxon_name}'

        taxon = self.get_taxonomy(
            taxon_name,
            taxon_name,
            _safe_upper(current_rank)
        )

        # If we already have a parent or reached KINGDOM, stop.
        if taxon.parent or _safe_upper(taxon.rank) == 'KINGDOM':
            return taxon

        # Try to climb by using CSV hints
        climb_guard = 0
        rank_cursor = current_rank
        while climb_guard < 10:
            climb_guard += 1
            parent_rank_name = parent_rank(rank_cursor)
            if not parent_rank_name:
                break
            parent = self.get_parent(row, parent_rank_name)
            if parent:
                taxon.parent = parent
                taxon.save()
                break
            rank_cursor = parent_rank_name

        return taxon

    def synonym_key(self, field_key):
        return f'{SYNONYM} {field_key}'

    def process_data(self, row, taxon_group: TaxonGroup):
        """Process a single CSV row."""
        if not self.all_keys:
            for key in row.keys():
                self.all_keys[key.upper()] = key

        auto_validate = preferences.SiteSetting.auto_validate_taxa_on_upload
        use_proposal = not auto_validate

        taxonomic_status = _safe_strip(self.get_row_value(row, TAXONOMIC_STATUS))
        taxon_name = _safe_strip(self.get_row_value(row, TAXON))
        accepted_taxon = None

        # Rank
        rank = self.get_row_value(row, TAXON_RANK)
        rank = RANK_TITLE.get(_safe_upper(rank), str(rank).capitalize() if rank else '')
        if rank.startswith('Sub'):
            rank = 'Sub' + rank[len('sub'):].capitalize()

        if not rank:
            rank = self.get_row_value(row, 'Taxon rank')
        if not rank:
            self.handle_error(row=row, message='Missing taxon rank')
            return

        if not taxon_name:
            taxon_name = _safe_strip(self.get_row_value(row, RANK_TITLE.get(_safe_upper(rank), str(rank).capitalize())))

        if 'species' in str(rank).lower():
            taxon_name = self._compose_species_name(row)

        if rank == SUBSPECIES:
            sub_species_name = _safe_strip(self.get_row_value(row, SUBSPECIES))
            if sub_species_name and taxon_name not in sub_species_name and not sub_species_name[0].isupper():
                taxon_name = f'{taxon_name} {sub_species_name}'

        # on_gbif flag
        raw_on_gbif = self.get_row_value(row, ON_GBIF)
        if raw_on_gbif is None:
            on_gbif = False if is_fada_site() else True
        else:
            on_gbif = 'yes' in raw_on_gbif.lower()

        if not taxon_name:
            self.handle_error(row=row, message='Missing Taxon value')
            return

        # GBIF key
        gbif_key = None
        if on_gbif:
            gbif_link = self.get_row_value(row, GBIF_LINK) or self.get_row_value(row, GBIF_URL)
            if gbif_link:
                last = str(gbif_link).rstrip('/').split('/')[-1]
                gbif_key = last[:-2] if last.endswith('.0') else last

        # FADA id (integer part)
        fada_id = self.get_row_value(row, FADA_ID)
        if fada_id:
            try:
                integer_part = str(fada_id).split('.', 1)[0]
                if integer_part and integer_part != '0':
                    fada_id = int(integer_part)
                else:
                    fada_id = None
            except ValueError:
                fada_id = None

        # Synonym support
        if 'synonym' in taxonomic_status.lower().strip():
            accepted_taxon_val = self.get_row_value(row, ACCEPTED_TAXON)
            if accepted_taxon_val:
                accepted_taxon = Taxonomy.objects.filter(
                    canonical_name__iexact=accepted_taxon_val
                ).first()

        authors = _safe_strip(self.get_row_value(row, AUTHORS))

        species_group = self.get_row_value(row, SPECIES_GROUP)
        if species_group:
            species_group, _ = SpeciesGroup.objects.get_or_create(name=species_group)

        # Scientific name + authorship
        if SCIENTIFIC_NAME in row:
            scientific_name = _safe_strip(self.get_row_value(row, SCIENTIFIC_NAME) or taxon_name)
        else:
            scientific_name = taxon_name

        if authors and authors not in scientific_name:
            scientific_name = f'{scientific_name} {authors}'.strip()

        # Parent check: parent must not have same name as the taxon
        parent = self.get_parent(row, parent_rank(rank))
        if parent and _safe_strip(parent.canonical_name) == taxon_name:
            self.handle_error(row=row, message='Parent cannot have the same name as the taxon')
            return

        # Resolve existing taxa (by gbif, fada, or canonical)
        taxa = Taxonomy.objects.none()
        if gbif_key:
            taxa = Taxonomy.objects.filter(gbif_key=gbif_key)
        if not taxa and fada_id:
            taxa = Taxonomy.objects.filter(fada_id=fada_id)
        if not taxa:
            taxa = Taxonomy.objects.filter(canonical_name__iexact=taxon_name)

        update_canonical_name = False
        if not taxa.exists() and ' ' in taxon_name:
            orphan = taxon_name.split(' ', 1)[1].strip()
            taxa = Taxonomy.objects.filter(
                canonical_name__iexact=orphan,
                rank=_safe_upper(rank)
            )
            update_canonical_name = taxa.exists()

        proposal = None
        new_taxon = False

        if taxa.exists() and update_canonical_name:
            obtained = taxa.first()
            obtained.canonical_name = taxon_name
            obtained.scientific_name = scientific_name
            obtained.save()

        try:
            taxonomy = None

            common_name_objs = self.common_name(row)
            should_fetch_vernacular_names = common_name_objs is None

            if taxa.exists():
                taxa_same_rank = taxa.filter(rank=_safe_upper(rank))
                taxonomy = taxa_same_rank.first() if taxa_same_rank.exists() else taxa.first()
                if taxonomy.rank != _safe_upper(rank):
                    logger.debug('%s has different RANK', taxon_name)
                    taxonomy.rank = _safe_upper(rank)

                logger.debug('%s already in the system', taxon_name)

            if not taxonomy and gbif_key:
                taxonomy = fetch_all_species_from_gbif(
                    gbif_key=gbif_key,
                    fetch_vernacular_names=should_fetch_vernacular_names
                )
                if taxonomy:
                    new_taxon = True

            if not taxonomy and on_gbif:
                taxonomy = fetch_all_species_from_gbif(
                    species=taxon_name,
                    taxonomic_rank=rank,
                    fetch_children=False,
                    fetch_vernacular_names=should_fetch_vernacular_names,
                    use_name_lookup=False
                )
                if taxonomy:
                    new_taxon = True

            # Ensure we have a taxonomy; if GBIF didn't return, construct one with a valid parent
            if not taxonomy:
                # Climb until we find a CSV-provided ancestor
                max_try = 10
                current_try = 0
                parent_name = parent_rank(rank)
                while not self.get_row_value(row, parent_name) and parent_name != KINGDOM and current_try < max_try:
                    current_try += 1
                    parent_name = parent_rank(parent_name)

                parent = self.get_parent(row, parent_name)
                if not parent:
                    self.handle_error(row=row, message='Data not found from GBIF for this taxon and its parents')
                    return
                new_taxon = True
                taxonomy, _ = Taxonomy.objects.get_or_create(
                    scientific_name=scientific_name,
                    canonical_name=taxon_name,
                    rank=TaxonomicRank[_safe_upper(rank)].name,
                    parent=parent
                )
                if taxonomic_status:
                    taxonomy.taxonomic_status = taxonomic_status.upper()

            # Backfill parent and author if missing
            if taxonomy and not taxonomy.parent and parent:
                taxonomy.parent = parent

            if on_gbif and taxonomy and not _safe_strip(getattr(taxonomy, 'author', '')):
                refreshed = fetch_all_species_from_gbif(
                    species=taxon_name,
                    taxonomic_rank=rank,
                    fetch_children=False,
                    fetch_vernacular_names=should_fetch_vernacular_names,
                    use_name_lookup=False
                )
                taxonomy = refreshed or taxonomy

            # Create proposal only once taxonomy exists and we know we need it
            if use_proposal:
                proposal = create_taxon_proposal(taxonomy, taxon_group)

            # Merge legacy canonical names
            legacy_canonical_name = (taxonomy.legacy_canonical_name or '').replace('\\xa0', '')
            if FORMER_SPECIES_NAME in row:
                former_species_name = _safe_strip(self.get_row_value(row, FORMER_SPECIES_NAME))
                if former_species_name:
                    former_species_name = former_species_name[:500]
                    if former_species_name not in legacy_canonical_name:
                        legacy_canonical_name = f'{legacy_canonical_name};{former_species_name}' if legacy_canonical_name else former_species_name

            self._update_taxon_and_proposal(
                taxonomy, proposal, use_proposal, new_taxon,
                'legacy_canonical_name', legacy_canonical_name[:700]
            )

            # Validate parents
            if new_taxon or not use_proposal:
                ok, message = self.validate_parents(taxon=taxonomy, row=row)
                if not ok:
                    self.handle_error(row=row, message=message)
                    return
            if use_proposal and proposal:
                ok, message = self.validate_parents(taxon=proposal, row=row)
                if not ok:
                    self.handle_error(row=row, message=message)
                    return

            # Endemism
            endemism_obj = self.endemism(row)
            if endemism_obj:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'endemism', endemism_obj)

            # Conservation (global + national)
            iucn_status = self.conservation_status(row, True)
            self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'iucn_status', iucn_status)

            national_cons_status = self.conservation_status(row, False)
            if national_cons_status:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'national_conservation_status', national_cons_status)

            # References
            msg, reference = self.source_reference(row)
            if msg and not reference:
                self.handle_error(row=row, message=msg)
                return
            if reference:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'source_reference', reference)

            # Common names
            if common_name_objs:
                if new_taxon or not use_proposal:
                    taxonomy.vernacular_names.clear()
                    for vn in common_name_objs:
                        taxonomy.vernacular_names.add(vn)
                if use_proposal and proposal:
                    proposal.vernacular_names.clear()
                    for vn in common_name_objs:
                        proposal.vernacular_names.add(vn)
            else:
                if taxonomy and taxonomy.gbif_key:
                    if new_taxon or not use_proposal:
                        fetch_gbif_vernacular_names(taxonomy)
                    if use_proposal and proposal:
                        fetch_gbif_vernacular_names(proposal)

            # Origin / invasion
            origin_data, invasion = self.origin(row)
            if origin_data:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'origin', origin_data)
            if invasion:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'invasion', invasion)

            # Author(s)
            if authors:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'author', authors)

            # SpeciesGroup
            if species_group:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'species_group', species_group)

            if fada_id and isinstance(fada_id, int):
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'fada_id', fada_id)

            if gbif_key:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'gbif_key', gbif_key)

            # Tags + biographic distributions
            if new_taxon or not use_proposal:
                taxonomy.tags.clear()
                taxonomy.biographic_distributions.clear()
            if use_proposal and proposal:
                proposal.tags.clear()
                proposal.biographic_distributions.clear()

            for key in row:
                row_value = self.get_row_value(row, key)
                val_norm = _safe_strip(row_value)
                if val_norm and (val_norm == '?' or _as_truthy(val_norm)):
                    tag_label = _norm_key_label(key)
                    if any(tag_label.lower() == bd.lower() for bd in BIOGRAPHIC_DISTRIBUTIONS):
                        doubtful = (val_norm == '?')
                        try:
                            taxon_tag, _ = TaxonTag.objects.get_or_create(
                                name=tag_label, defaults={'doubtful': doubtful}
                            )
                        except TaxonTag.MultipleObjectsReturned:
                            taxon_tag = TaxonTag.objects.filter(name=tag_label, doubtful=doubtful).order_by('id').first() or TaxonTag.objects.filter(name=tag_label).order_by('id').first()
                        if new_taxon or not use_proposal:
                            taxonomy.biographic_distributions.add(taxon_tag)
                        if use_proposal and proposal:
                            proposal.biographic_distributions.add(taxon_tag)
                    elif val_norm != '?':
                        if new_taxon or not use_proposal:
                            taxonomy.tags.add(tag_label)
                        if use_proposal and proposal:
                            proposal.tags.add(tag_label)

            # Additional data
            try:
                addl = json.dumps(row)
            except TypeError:
                # Fallback: stringify
                addl = json.dumps({str(k): str(v) for k, v in row.items()})
            self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'additional_data', addl)

            if taxonomy.canonical_name != taxon_name:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'canonical_name', taxon_name)

            if taxonomic_status:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'taxonomic_status', taxonomic_status.strip().upper())

            if accepted_taxon:
                self._update_taxon_and_proposal(taxonomy, proposal, use_proposal, new_taxon, 'accepted_taxonomy', accepted_taxon)

            taxonomy.save()
            if proposal:
                proposal.save()

            # Taxon group linking (respects auto-validate in subclass)
            self.add_taxon_to_taxon_group_unvalidated(taxonomy, taxon_group)

            self.finish_processing_row(row, taxonomy)

        except Exception as e:  # noqa
            logger.exception('Error processing row for "%s": %s', taxon_name, e)
            self.handle_error(row, str(e))


class TaxaCSVUpload(DataCSVUpload, TaxaProcessor):
    model_name = 'taxonomy'

    def add_taxon_to_taxon_group_unvalidated(self, taxonomy, taxon_group, proposal=None):
        """
        Respect site preference: auto_validate_taxa_on_upload
        """
        auto_validate = preferences.SiteSetting.auto_validate_taxa_on_upload
        self.add_taxon_to_taxon_group(taxonomy, taxon_group, validated=auto_validate)

    def finish_processing_row(self, row, taxonomy):
        # Add to taxon group if missing
        taxon_group = self.upload_session.module_group
        if not taxon_group.taxonomies.filter(id=taxonomy.id).exists():
            taxon_group.taxonomies.add(taxonomy)

        # Import date
        taxonomy.import_date = self.upload_session.uploaded_at.date()
        taxonomy.save()

        self.success_file(row, taxonomy.id)

    def handle_error(self, row, message):
        self.error_file(error_row=row, error_message=message)

    def process_row(self, row):
        taxon_group = self.upload_session.module_group
        with transaction.atomic():
            self.process_data(row, taxon_group)
