import logging

from django.db import IntegrityError, transaction
from django.db.models.fields.related import ForeignObjectRel
from bims.utils.gbif import (
    get_children, find_species, get_species, get_vernacular_names,
    gbif_name_suggest
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


def create_or_update_taxonomy(
        gbif_data,
        fetch_vernacular_names=False):
    """
    Create or update taxonomy data from gbif response data
    :param gbif_data: gbif response data
    :param fetch_vernacular_names: should fetch vernacular names
    """
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
            return fetch_all_species_from_gbif(
                gbif_key=parent_key,
                fetch_children=False
            )
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
    if 'oldKey' in gbif_data:
        taxa = Taxonomy.objects.filter(
            gbif_key=gbif_data['oldKey']
        )
    if not taxa:
        taxa = Taxonomy.objects.filter(
            gbif_key=gbif_data['key']
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

    if fetch_vernacular_names:
        fetch_gbif_vernacular_names(taxonomy)
    taxonomy.save()
    return taxonomy


def fetch_all_species_from_gbif(
    species='',
    taxonomic_rank=None,
    gbif_key=None,
    parent=None,
    fetch_children=False,
    fetch_vernacular_names=False,
    use_name_lookup=True,
    log_file_path=None,
    _visited=None,
    _depth=0,
    **classifier):
    """
    Get species detail and all lower rank species
    :param species: species name
    :param taxonomic_rank: taxonomy rank e.g. class
    :param gbif_key: gbif key
    :param parent: taxonomy parent
    :param fetch_children: fetch children or not
    :param fetch_vernacular_names: fetch vernacular names or not
    :param use_name_lookup: use name_lookup to search species
    :return:
    """
    def log_info(message: str):
        logger.info(message)
        if log_file_path:
            with open(log_file_path, 'a') as log_file:
                log_file.write('{}\n'.format(message))

    if _visited is None:
        _visited = set()

    if _depth > MAX_DEPTH:
        log_info(f"Depth>{MAX_DEPTH} for key={gbif_key} – aborting to avoid recursion loop")
        return None

    if gbif_key:
        if gbif_key in _visited:
            log_info(f"Cycle detected at key={gbif_key}; skipping further recursion")
            existing = Taxonomy.objects.filter(gbif_key=gbif_key).first()
            return existing
        _visited.add(gbif_key)
        log_info('Get species {gbif_key}'.format(
            gbif_key=gbif_key
        ))
        species_data = None
        taxon = None

        try:
            taxon = Taxonomy.objects.get(gbif_key=gbif_key)
            species_data = taxon.gbif_data
        except Taxonomy.MultipleObjectsReturned:
            taxa = Taxonomy.objects.filter(gbif_key=gbif_key)
            taxon = taxa.first()
            merge_taxa_data(
                excluded_taxon=taxon,
                taxa_list=taxa.exclude(id=taxon.id)
            )
            species_data = taxon.gbif_data
        except Taxonomy.DoesNotExist:
            pass

        gbif_data = get_species(gbif_key)
        if gbif_data:
            if taxon:
                taxon.gbif_data = gbif_data
                taxon.save()
            species_data = gbif_data
    else:
        log_info('Fetching {species} - {rank}'.format(
            species=species,
            rank=taxonomic_rank,
        ))
        if use_name_lookup:
            species_data = find_species(
                original_species_name=species,
                rank=taxonomic_rank,
                returns_all=False,
                **classifier)
        else:
            species_data = gbif_name_suggest(
                q=species,
                rank=taxonomic_rank
            )

    raw_rank = species_data.get('rank', '').upper() if species_data else ''
    if raw_rank == "UNRANKED":
        parent_key = (species_data or {}).get("parentKey")
        if parent_key and parent_key != species_data.get("key") and parent_key not in _visited:
            log_info(
                f"UNRANKED record {species_data.get('key')}; "
                f"resolving to parent {parent_key}")
            return fetch_all_species_from_gbif(
                gbif_key=parent_key,
                fetch_children=False,
                fetch_vernacular_names=fetch_vernacular_names,
                use_name_lookup=use_name_lookup,
                log_file_path=log_file_path,
                _visited=_visited,
                _depth=_depth + 1,
            )
        log_info(
            f"Skipping UNRANKED record (no safe parent) – "
            f"GBIF key {species_data.get('key') if species_data else None}")
        return None

    # if species not found then return nothing
    if not species_data:
        log_info('Species not found')
        return None

    legacy_name = species

    # Check if nubKey is identical with the key
    # if not then fetch the species with the nubKey to get a better data
    rank_key = None
    if taxonomic_rank:
        rank_key = '{}Key'.format(taxonomic_rank.lower())
    if ('nubKey' in species_data or rank_key) and taxonomic_rank:
        if gbif_key:
            if isinstance(gbif_key, str):
                gbif_key = int(gbif_key)
            temp_key = gbif_key
        else:
            temp_key = species_data['key']
        if 'nubKey' in species_data:
            nub_key = species_data['nubKey']
            if nub_key != temp_key:
                old_key = nub_key
                new_species_data = get_species(nub_key)
                if new_species_data['rank']:
                    if new_species_data['rank'].upper() == taxonomic_rank.upper():
                        species_data = new_species_data
                        species_data['oldKey'] = old_key
        else:
            if rank_key in species_data:
                old_key = species_data['key']
                if old_key != species_data[rank_key]:
                    new_species_data = get_species(species_data[rank_key])
                    if (
                            new_species_data[
                                'rank'].upper() == taxonomic_rank.upper()
                    ):
                        species_data = new_species_data
                        species_data['oldKey'] = old_key

    logger.debug(species_data)
    if not species_data:
        return None
    if 'authorship' not in species_data and 'nubKey' in species_data:
        species_data = get_species(species_data['nubKey'])
    taxonomy = create_or_update_taxonomy(species_data, fetch_vernacular_names)
    if not taxonomy:
        log_info('Taxonomy not updated/created')
        return None
    species_key = taxonomy.gbif_key
    scientific_name = taxonomy.scientific_name

    if parent:
        taxonomy.parent = parent
        taxonomy.save()
    else:
        desired_parent_key = (species_data or {}).get('parentKey')
        need_fetch_parent = (
            desired_parent_key
            and (not taxonomy.parent or taxonomy.parent.gbif_key != desired_parent_key)
        )
        if need_fetch_parent and desired_parent_key != taxonomy.gbif_key and desired_parent_key not in _visited:
            log_info(f'Get parent with parentKey : {desired_parent_key}')
            parent_taxonomy = fetch_all_species_from_gbif(
                gbif_key=desired_parent_key,
                parent=None,
                fetch_children=False,
                fetch_vernacular_names=fetch_vernacular_names,
                use_name_lookup=use_name_lookup,
                log_file_path=log_file_path,
                _visited=_visited,
                _depth=_depth + 1,
            )
            if parent_taxonomy:
                taxonomy.parent = parent_taxonomy
                taxonomy.save()

    max_tries = 20
    tries = 0
    cursor = taxonomy
    while tries < max_tries and cursor and cursor.rank and cursor.rank.lower() != 'kingdom':
        if not cursor.parent:
            pk = (cursor.gbif_data or {}).get('parentKey') if hasattr(cursor, 'gbif_data') else None
            if pk and pk != cursor.gbif_key and pk not in _visited:
                pt = fetch_all_species_from_gbif(
                    gbif_key=pk,
                    parent=None,
                    fetch_children=False,
                    fetch_vernacular_names=fetch_vernacular_names,
                    use_name_lookup=use_name_lookup,
                    log_file_path=log_file_path,
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

    # Check if there is an accepted key
    try:
        status = (species_data.get('taxonomicStatus') or "").strip().lower()
    except Exception:
        status = ""
    if species_data and 'acceptedKey' in species_data and 'synonym' in status:
        ak = species_data['acceptedKey']
        if ak and ak != taxonomy.gbif_key and ak not in _visited:
            accepted_taxonomy = fetch_all_species_from_gbif(
                gbif_key=ak,
                taxonomic_rank=taxonomy.rank,
                parent=taxonomy.parent,
                fetch_children=False,
                fetch_vernacular_names=fetch_vernacular_names,
                use_name_lookup=use_name_lookup,
                log_file_path=log_file_path,
                _visited=_visited,
                _depth=_depth + 1,
            )
            if accepted_taxonomy:
                if taxonomy.iucn_status:
                    accepted_taxonomy.iucn_status = taxonomy.iucn_status
                    accepted_taxonomy.save()
                taxonomy.accepted_taxonomy = accepted_taxonomy
                taxonomy.save()

    if not fetch_children:
        if taxonomy.legacy_canonical_name:
            legacy_canonical_name = taxonomy.legacy_canonical_name
            if legacy_name not in legacy_canonical_name:
                legacy_canonical_name += ';' + legacy_name
        else:
            legacy_canonical_name = legacy_name
        taxonomy.legacy_canonical_name = legacy_canonical_name
        taxonomy.save()
        return taxonomy

    if species_key and scientific_name:
        log_info('Get children from : {}'.format(species_key))
        children = get_children(species_key)
        if not children:
            return taxonomy
        for child in children:
            try:
                children_key = child['nubKey']
            except KeyError:
                children_key = child['key']
            fetch_all_species_from_gbif(
                gbif_key=children_key,
                species=child['scientificName'],
                parent=taxonomy
            )

    return taxonomy
