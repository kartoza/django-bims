import logging

import requests
from django.db import IntegrityError, transaction
from django.db.models.fields.related import ForeignObjectRel

from bims.scripts.species_keys import RANK_INDEX
from bims.utils.gbif import (
    get_children, find_species, get_species, get_vernacular_names,
    gbif_name_suggest, gbif_synonyms_by_usage, get_species_by_col_id
)
from bims.models import Taxonomy, VernacularName, TaxonGroup
from bims.enums import TaxonomicRank, TaxonomicStatus

logger = logging.getLogger('bims')
MAX_DEPTH = 50


def merge_taxa_data(gbif_key='', excluded_taxon=None, taxa_list=None):
    """
    If there are more than one data with same gbif key,
    then merge those data
    """
    if not excluded_taxon:
        return
    if taxa_list:
        taxa = taxa_list
    else:
        taxa = Taxonomy.objects.filter(
            gbif_key=gbif_key
        )

    taxa = taxa.exclude(id=excluded_taxon.id)

    if taxa.count() < 1:
        return

    logger.info('Merging %s data' % len(taxa))

    taxon_groups = TaxonGroup.objects.filter(
        taxonomies__in=taxa
    )

    for taxon_group in taxon_groups:
        taxon_group.taxonomies.add(excluded_taxon)

    vernacular_names = []

    links = [
        rel.get_accessor_name() for rel in excluded_taxon._meta.get_fields() if
        issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for taxon in taxa:
            if taxon.vernacular_names.all().exists():
                vernacular_names.extend(
                    list(
                        taxon.vernacular_names.all())
                )
            logger.info('----- {} -----'.format(str(taxon)))
            for link in links:
                if link == 'taxongrouptaxonomy_set':
                    continue
                try:
                    with transaction.atomic():
                        objects = getattr(taxon, link).all()
                        if objects.count() > 0:
                            print('Updating {obj} for : {taxon}'.format(
                                obj=str(objects.model._meta.label),
                                taxon=str(taxon)
                            ))
                            update_dict = {
                                getattr(taxon, link).field.name: excluded_taxon
                            }
                            objects.update(**update_dict)
                except Exception as e:  # noqa
                    logger.error(e)
                    continue
            logger.info(''.join(['-' for i in range(len(str(taxon)) + 12)]))

    taxa.delete()

    if vernacular_names:
        excluded_taxon.vernacular_names.add(*vernacular_names)


def _norm(s: str) -> str:
    return (s or "").strip()


def fetch_gbif_vernacular_names(taxonomy):
    if not getattr(taxonomy, "gbif_key", None):
        return False

    vernacular_names = get_vernacular_names(taxonomy.gbif_key)
    logger.info("Fetching vernacular names for %s", taxonomy.canonical_name)

    results = (vernacular_names or {}).get("results") or []
    if not results:
        logger.info("Found 0 vernacular names")
        return True

    logger.info("Found %s vernacular names", len(results))

    order_val = 1
    created_cnt = 0
    updated_cnt = 0

    for result in results:
        name_clean = _norm(result.get("vernacularName"))
        if not name_clean:
            continue

        source_clean   = _norm(result.get("source"))
        language_clean = _norm(result.get("language")) or None

        fields = {
            "language": language_clean,
            "order": order_val,
        }
        if result.get("taxonKey") is not None:
            try:
                fields["taxon_key"] = int(result["taxonKey"])
            except (TypeError, ValueError):
                pass

        obj = None

        try:
            with transaction.atomic():
                obj = (VernacularName.objects
                       .filter(name__iexact=name_clean, source=source_clean)
                       .order_by('id')
                       .first())
                if obj:
                    changed = []
                    for k, v in fields.items():
                        if getattr(obj, k) != v:
                            setattr(obj, k, v)
                            changed.append(k)
                    if changed:
                        obj.save(update_fields=changed)
                    updated_cnt += 1
                else:
                    obj = VernacularName.objects.create(
                        name=name_clean,
                        source=source_clean,
                        **fields,
                    )
                    created_cnt += 1

        except IntegrityError as ie:
            logger.warning(
                "IntegrityError creating VernacularName(name=%r, source=%r): %s",
                name_clean, source_clean, ie
            )
            obj = (VernacularName.objects
                   .filter(name__iexact=name_clean, source=source_clean)
                   .order_by('id')
                   .first())
            if obj:
                changed = []
                for k, v in fields.items():
                    if getattr(obj, k) != v:
                        setattr(obj, k, v)
                        changed.append(k)
                if changed:
                    obj.save(update_fields=changed)
                updated_cnt += 1
            else:
                with transaction.atomic():
                    obj, created = VernacularName.objects.get_or_create(
                        name=name_clean,
                        source=source_clean,
                        defaults=fields
                    )
                    if created:
                        created_cnt += 1
                    else:
                        changed = []
                        for k, v in fields.items():
                            if getattr(obj, k) != v:
                                setattr(obj, k, v)
                                changed.append(k)
                        if changed:
                            obj.save(update_fields=changed)
                        updated_cnt += 1

        taxonomy.vernacular_names.add(obj)
        order_val += 1

    taxonomy.save()
    logger.info(
        "Vernacular names linked. created=%d updated=%d",
        created_cnt, updated_cnt
    )
    return True


def _create_or_update_from_col(col_data, fetch_vernacular_names=False, preserve_taxonomic_status=False):
    """Create or update Taxonomy from a COL v2 match API response."""
    usage = col_data.get('usage', {})
    col_id = str(usage.get('key') or '')
    canonical_name = usage.get('canonicalName', '')
    scientific_name = usage.get('name', '') or canonical_name
    author = usage.get('authorship', '')
    raw_rank = (usage.get('rank') or '').upper()
    status_str = (usage.get('status') or '').upper()

    if not canonical_name and not scientific_name:
        logger.error('COL response missing name fields: %s', col_data)
        return None
    if not raw_rank:
        logger.error('COL response missing rank: %s', col_data)
        return None

    rank_enum = TaxonomicRank.__members__.get(raw_rank)
    rank = rank_enum.name if rank_enum else raw_rank

    try:
        taxonomic_status = TaxonomicStatus[status_str].name
    except KeyError:
        taxonomic_status = ''

    clean_data = _clean_col_data(col_data)

    taxa = None
    if col_id:
        taxa = Taxonomy.objects.filter(col_id=col_id)
    if not taxa or not taxa.exists():
        taxa = Taxonomy.objects.filter(
            scientific_name=scientific_name,
            canonical_name=canonical_name,
            rank=rank,
        )

    if not taxa or not taxa.exists():
        taxonomy = Taxonomy.objects.create(
            scientific_name=scientific_name,
            canonical_name=canonical_name,
            taxonomic_status=taxonomic_status,
            rank=rank,
        )
    else:
        if preserve_taxonomic_status:
            existing_status = taxa[0].taxonomic_status
            update_fields = {
                'scientific_name': scientific_name,
                'canonical_name': canonical_name,
                'rank': rank,
            }
            if not existing_status:
                update_fields['taxonomic_status'] = taxonomic_status
            taxa.update(**update_fields)
        else:
            taxa.update(
                scientific_name=scientific_name,
                canonical_name=canonical_name,
                taxonomic_status=taxonomic_status,
                rank=rank,
            )
        taxonomy = taxa[0]

    if author:
        taxonomy.author = author
    if col_id and not taxonomy.col_id:
        taxonomy.col_id = col_id
    taxonomy.gbif_data = clean_data

    if fetch_vernacular_names:
        fetch_gbif_vernacular_names(taxonomy)
    taxonomy.save()
    return taxonomy


def create_or_update_taxonomy(
        gbif_data,
        fetch_vernacular_names=False,
        preserve_taxonomic_status=False):
    """
    Create or update taxonomy data from gbif response data
    :param gbif_data: gbif response data
    :param fetch_vernacular_names: should fetch vernacular names
    :param preserve_taxonomic_status: if True, preserve existing taxonomic_status from CSV (FADA use case)
    """
    if gbif_data and 'usage' in gbif_data:
        return _create_or_update_from_col(gbif_data, fetch_vernacular_names, preserve_taxonomic_status)

    taxa = None
    try:
        species_key = gbif_data['nubKey']
    except KeyError:
        species_key = gbif_data['key']

    raw_rank = gbif_data.get('rank', '').upper()

    if raw_rank == "UNRANKED":
        parent_key = gbif_data.get("parentKey")
        if parent_key:
            logger.debug("UNRANKED record %s; resolving to parent %s", gbif_data.get("key"), parent_key)
            parent_data = get_species(parent_key)
            if parent_data:
                return create_or_update_taxonomy(parent_data, fetch_vernacular_names, preserve_taxonomic_status)
        logger.debug("Skipping UNRANKED record (no parentKey) – GBIF key %s", gbif_data.get("key"))
        return None

    rank_enum = TaxonomicRank.__members__.get(raw_rank)
    rank = rank_enum.name if rank_enum else raw_rank

    if not raw_rank:
        logger.error("GBIF record has no 'rank' field: %s", gbif_data)
        return None
    if 'scientificName' not in gbif_data:
        logger.error('No scientificName')
        return None
    if 'canonicalName' not in gbif_data:
        logger.error('No canonicalName')
        return None
    canonical_name = gbif_data['canonicalName']
    scientific_name = gbif_data['scientificName']
    taxonomic_status = ''
    if 'taxonomicStatus' in gbif_data:
        taxonomic_status = gbif_data['taxonomicStatus']
    elif 'status' in gbif_data:
        taxonomic_status = gbif_data['status']
    try:
        taxonomic_status = TaxonomicStatus[
            taxonomic_status].name
    except KeyError:
        taxonomic_status = ''
    taxon_key_raw = str(gbif_data.get('taxonKey') or '')
    col_id_from_data = taxon_key_raw if (taxon_key_raw and not taxon_key_raw.isdigit()) else None

    if 'oldKey' in gbif_data:
        taxa = Taxonomy.objects.filter(
            gbif_key=gbif_data['oldKey']
        )
    if not taxa:
        taxa = Taxonomy.objects.filter(
            gbif_key=gbif_data['key']
        )
    if not taxa and col_id_from_data:
        taxa = Taxonomy.objects.filter(
            col_id=col_id_from_data
        )
    if not taxa:
        taxa = Taxonomy.objects.filter(
            scientific_name=scientific_name,
            canonical_name=canonical_name,
            taxonomic_status=taxonomic_status,
            rank=rank,
        )
    if not taxa.exists():
        taxonomy = Taxonomy.objects.create(
            scientific_name=scientific_name,
            canonical_name=canonical_name,
            taxonomic_status=taxonomic_status,
            rank=rank,
        )
    else:
        # For FADA sites, preserve existing taxonomic_status from CSV
        if preserve_taxonomic_status:
            existing_status = taxa[0].taxonomic_status
            update_fields = {
                'scientific_name': scientific_name,
                'canonical_name': canonical_name,
                'rank': rank,
            }
            # Only update taxonomic_status if it's empty
            if not existing_status:
                update_fields['taxonomic_status'] = taxonomic_status
            taxa.update(**update_fields)
        else:
            taxa.update(
                scientific_name=scientific_name,
                canonical_name=canonical_name,
                taxonomic_status=taxonomic_status,
                rank=rank,
            )
        taxonomy = taxa[0]
    if 'authorship' in gbif_data:
        taxonomy.author = gbif_data['authorship']
    taxonomy.gbif_key = species_key
    taxonomy.gbif_data = gbif_data

    if col_id_from_data and not taxonomy.col_id:
        taxonomy.col_id = col_id_from_data

    if fetch_vernacular_names:
        fetch_gbif_vernacular_names(taxonomy)
    taxonomy.save()
    return taxonomy


_RANK_PARENT = {
    'SPECIES': 'GENUS',
    'SUBSPECIES': 'SPECIES',
    'VARIETY': 'SPECIES',
    'SUBVARIETY': 'SPECIES',
    'FORM': 'SPECIES',
    'SUBFORM': 'SPECIES',
    'GENUS': 'FAMILY',
    'FAMILY': 'ORDER',
    'ORDER': 'CLASS',
    'CLASS': 'PHYLUM',
    'PHYLUM': 'KINGDOM',
}


def _parent_col_id_from_classification(classification):
    """Return the COL ID of the immediate parent from a classification list."""
    if not classification or len(classification) == 1:
        return None
    parent = list(reversed(classification))[1]
    return parent.get('key', None)


def _clean_col_data(col_data):
    """Strip diagnostics and additionalStatus before persisting."""
    if not col_data:
        return col_data
    return {k: v for k, v in col_data.items() if k not in ('diagnostics', 'additionalStatus')}


def fetch_all_species_from_gbif(
    species='',
    taxonomic_rank=None,
    col_id=None,
    col_row=None,
    parent=None,
    fetch_children=False,
    fetch_vernacular_names=False,
    use_name_lookup=True,
    is_synonym=False,
    log_file_path=None,
    preserve_taxonomic_status=False,
    _visited=None,
    _depth=0,
    **classifier):
    """
    Get species detail from COL and create/update the local Taxonomy record.
    :param species: species name (used when col_id is not provided)
    :param taxonomic_rank: taxonomy rank e.g. SPECIES
    :param col_id: COL identifier - preferred lookup key
    :param col_row: full row dict from GBIF SPECIES_LIST download
    :param parent: explicit parent Taxonomy instance
    :param fetch_children: unused - COL match API does not support children listing
    :param fetch_vernacular_names: fetch vernacular names after save
    :param use_name_lookup: use find_species (True) or gbif_name_suggest (False)
    :param is_synonym: treat this taxon as a synonym
    :param preserve_taxonomic_status: if True, preserve existing taxonomic_status
    :return: Taxonomy instance or None
    """
    def log_info(message: str):
        logger.info(message)
        if log_file_path:
            with open(log_file_path, 'a') as log_file:
                log_file.write('{}\n'.format(message))

    if _visited is None:
        _visited = set()

    if _depth > MAX_DEPTH:
        log_info(f"Depth>{MAX_DEPTH} for col_id={col_id} – aborting to avoid recursion loop")
        return None

    source_taxonomic_status = 'accepted' if not is_synonym else 'synonym'
    species_data = None
    taxon = None

    if col_id:
        if col_id in _visited:
            log_info(f"Cycle detected at col_id={col_id}; skipping further recursion")
            return Taxonomy.objects.filter(col_id=col_id).first()
        _visited.add(col_id)
        log_info(f'Get species by COL ID: {col_id}')

        try:
            taxon = Taxonomy.objects.get(col_id=col_id)
            if taxonomic_rank and taxon.rank and taxon.rank.upper() != taxonomic_rank.upper():
                return None
            species_data = taxon.gbif_data
        except Taxonomy.MultipleObjectsReturned:
            taxa = Taxonomy.objects.filter(col_id=col_id)
            taxon = taxa.first()
            merge_taxa_data(excluded_taxon=taxon, taxa_list=taxa.exclude(id=taxon.id))
            species_data = taxon.gbif_data
        except Taxonomy.DoesNotExist:
            pass

        if not species_data:
            col_api_data = get_species_by_col_id(col_id)
            if col_api_data and 'usage' in col_api_data:
                species_data = col_api_data
                if taxon:
                    taxon.gbif_data = _clean_col_data(col_api_data)
                    taxon.save()

    elif species:
        log_info('Fetching {species} - {rank}'.format(species=species, rank=taxonomic_rank))
        if use_name_lookup:
            species_data = find_species(
                original_species_name=species,
                rank=taxonomic_rank,
                returns_all=False,
                **classifier)
        else:
            species_data = gbif_name_suggest(q=species, rank=taxonomic_rank)

        if species_data and species:
            col_canonical = (
                (species_data.get('usage') or {}).get('canonicalName') or
                species_data.get('canonicalName') or ''
            ).strip().lower()
            col_name = (
                (species_data.get('usage') or {}).get('name') or
                species_data.get('name') or ''
            ).strip().lower()
            input_name = species.strip().lower()
            if col_canonical and input_name and col_canonical != input_name and col_name != input_name:
                log_info(
                    f"COL name mismatch: input '{species}' does not match "
                    f"COL canonical name '{col_canonical}' - skipping"
                )
                return None
    else:
        log_info('No identifier or name provided')
        return None

    if not species_data:
        log_info('Species not found')
        return None

    usage = species_data.get('usage', {})
    raw_rank = (usage.get('rank') or species_data.get('rank', '')).upper()
    species_status = (
        usage.get('status') or
        species_data.get('taxonomicStatus') or
        species_data.get('status') or ''
    )

    if taxonomic_rank and raw_rank != taxonomic_rank.upper():
        return None

    if raw_rank == 'UNRANKED':
        classification = species_data.get('classification', [])
        parent_col_id = classification[-1].get('key') if classification else None
        if parent_col_id and parent_col_id not in _visited:
            log_info(f"UNRANKED record; resolving to classification parent {parent_col_id}")
            return fetch_all_species_from_gbif(
                col_id=parent_col_id,
                fetch_children=False,
                fetch_vernacular_names=fetch_vernacular_names,
                preserve_taxonomic_status=preserve_taxonomic_status,
                use_name_lookup=use_name_lookup,
                log_file_path=log_file_path,
                _visited=_visited,
                _depth=_depth + 1,
            )
        log_info(f"Skipping UNRANKED record (no parent) – col_id={col_id}")
        return None

    if preserve_taxonomic_status and species_status.lower() not in source_taxonomic_status:
        return None

    taxonomy = create_or_update_taxonomy(species_data, fetch_vernacular_names, preserve_taxonomic_status)

    if not taxonomy:
        log_info('Taxonomy not updated/created')
        return None

    scientific_name = taxonomy.scientific_name
    gbif_status_lower = species_status.strip().lower()

    if parent and not is_synonym:
        taxonomy.parent = parent
        taxonomy.save()
    elif not is_synonym:
        classification = species_data.get('classification', [])
        parent_col_id = _parent_col_id_from_classification(classification)

        need_fetch_parent = (
            parent_col_id
            and (not taxonomy.parent or taxonomy.parent.col_id != parent_col_id)
        )
        if need_fetch_parent and parent_col_id != taxonomy.col_id and parent_col_id not in _visited:
            log_info(f'Get parent with COL ID: {parent_col_id}')
            parent_taxonomy = fetch_all_species_from_gbif(
                col_id=parent_col_id,
                parent=None,
                fetch_children=False,
                fetch_vernacular_names=fetch_vernacular_names,
                use_name_lookup=use_name_lookup,
                log_file_path=log_file_path,
                preserve_taxonomic_status=preserve_taxonomic_status,
                _visited=_visited,
                _depth=_depth + 1,
            )
            if parent_taxonomy:
                taxonomy.parent = parent_taxonomy
                taxonomy.save()

    if not is_synonym:
        max_tries = 20
        tries = 0
        cursor = taxonomy
        while tries < max_tries and cursor and cursor.rank and cursor.rank.lower() != 'kingdom':
            if not cursor.parent:
                cursor_data = cursor.gbif_data or {}
                cursor_classification = cursor_data.get('classification', [])
                pk = _parent_col_id_from_classification(cursor_classification)
                if pk and pk != cursor.col_id and pk not in _visited:
                    pt = fetch_all_species_from_gbif(
                        col_id=pk,
                        parent=None,
                        fetch_children=False,
                        fetch_vernacular_names=fetch_vernacular_names,
                        use_name_lookup=use_name_lookup,
                        log_file_path=log_file_path,
                        preserve_taxonomic_status=preserve_taxonomic_status,
                        _visited=_visited,
                        _depth=_depth + 1,
                    )
                    if pt:
                        cursor.parent = pt
                        cursor.save()
                    else:
                        break
                else:
                    break
            cursor = cursor.parent
            tries += 1
    else:
        log_info(
            f'Skipping parent fetch for {gbif_status_lower} taxon '
            f'(col_id={taxonomy.col_id}, name={scientific_name})'
        )
        if taxonomy.parent:
            log_info(
                f'Detaching parent from {gbif_status_lower} taxon '
                f'(col_id={taxonomy.col_id}, name={scientific_name})'
            )
            taxonomy.parent = None
            taxonomy.save()

    if (
        is_synonym and
        not preserve_taxonomic_status and
        species_data and
        not taxonomy.accepted_taxonomy
    ):
        if col_id:
            ak = (
                species_data.get('acceptedUsage', {}).get(
                    'key', None
                )
            )
        else:
            usage = species_data.get('usage', {})
            ak = (
                usage.get('acceptedKey') or
                species_data.get('acceptedKey') or
                species_data.get('acceptedTaxonKey')
            )
        if ak and ak != taxonomy.col_id and ak not in _visited:
            accepted_preexists = Taxonomy.objects.filter(col_id=ak).exists()
            if accepted_preexists:
                accepted_taxonomy = Taxonomy.objects.filter(col_id=ak).first()
            else:
                accepted_taxonomy = fetch_all_species_from_gbif(
                    col_id=ak,
                    parent=taxonomy.parent,
                    fetch_children=False,
                    fetch_vernacular_names=fetch_vernacular_names,
                    use_name_lookup=use_name_lookup,
                    log_file_path=log_file_path,
                    preserve_taxonomic_status=preserve_taxonomic_status,
                    _visited=_visited,
                    _depth=_depth + 1,
                )
            if accepted_taxonomy:
                taxonomy.accepted_taxonomy = accepted_taxonomy
                taxonomy.save()

    legacy_name = species
    if taxonomy.legacy_canonical_name:
        legacy_canonical_name = taxonomy.legacy_canonical_name
        if legacy_name and legacy_name not in legacy_canonical_name:
            legacy_canonical_name += ';' + legacy_name
    else:
        legacy_canonical_name = legacy_name or ''
    taxonomy.legacy_canonical_name = legacy_canonical_name
    taxonomy.save()
    return taxonomy

def harvest_synonyms_for_accepted_taxonomy(
    accepted_taxonomy: Taxonomy,
    fetch_vernacular_names: bool = False,
    log_file_path: str | None = None,
    accept_language: str | None = None,
):
    """
    Harvest synonyms for a given *accepted* Taxonomy using GBIF's
    /v1/species/{usageKey}/synonyms endpoint.
    """
    def log_info(msg: str):
        logger.info(msg)
        if log_file_path:
            with open(log_file_path, "a") as f:
                f.write(msg + "\n")

    if not accepted_taxonomy or not getattr(accepted_taxonomy, "gbif_key", None):
        log_info("harvest_synonyms_for_accepted_taxonomy: missing accepted taxonomy or gbif_key")
        return []

    log_info(
        f"Harvesting synonyms via GBIF API for accepted taxonomy "
        f"{accepted_taxonomy.canonical_name} (key={accepted_taxonomy.gbif_key})"
    )

    try:
        synonyms_payload = gbif_synonyms_by_usage(
            usage_key=int(accepted_taxonomy.gbif_key),
            limit=1000,
            accept_language=accept_language,
        )
    except requests.RequestException as e:
        logger.error("Failed to fetch GBIF synonyms for key=%s: %s", accepted_taxonomy.gbif_key, e)
        return []

    if not synonyms_payload:
        log_info("No synonyms returned by GBIF for this accepted taxonomy.")
        return []

    processed: list[Taxonomy] = []
    seen_keys: set[int] = set()
    allowed_status_substrings = ("SYNONYM",)

    for syn in synonyms_payload:
        syn_key = syn.get("nubKey") or syn.get("key")
        try:
            syn_key_int = int(syn_key) if syn_key is not None else None
        except (TypeError, ValueError):
            syn_key_int = None

        if not syn_key_int:
            continue
        if syn_key_int == accepted_taxonomy.gbif_key or syn_key_int in seen_keys:
            continue
        seen_keys.add(syn_key_int)

        status = (syn.get("taxonomicStatus") or syn.get("status") or "").upper()
        if not any(tag in status for tag in allowed_status_substrings):
            continue

        minimal_ok = all(k in syn for k in ("scientificName", "canonicalName", "rank"))
        syn_full = syn if minimal_ok else (get_species(syn_key_int) or syn)

        synonym_tax = create_or_update_taxonomy(
            syn_full,
            fetch_vernacular_names=fetch_vernacular_names,
        )
        if not synonym_tax:
            log_info(f"Failed to create/update synonym taxonomy for key={syn_key_int}")
            continue

        changed = False
        if getattr(synonym_tax, "accepted_taxonomy_id", None) != accepted_taxonomy.id:
            synonym_tax.accepted_taxonomy = accepted_taxonomy
            changed = True

        if changed:
            synonym_tax.save()

        processed.append(synonym_tax)
        log_info(
            f"Linked synonym {synonym_tax.canonical_name} "
            f"(key={synonym_tax.gbif_key}) → accepted {accepted_taxonomy.canonical_name}"
        )

    log_info(f"Synonyms processed: {len(processed)}")
    return processed
