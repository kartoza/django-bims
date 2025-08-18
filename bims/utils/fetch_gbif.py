import logging
from django.db.models.fields.related import ForeignObjectRel
from bims.utils.gbif import (
    get_children, find_species, get_species, get_vernacular_names,
    gbif_name_suggest
)
from bims.models import Taxonomy, VernacularName, TaxonGroup
from bims.enums import TaxonomicRank, TaxonomicStatus

logger = logging.getLogger('bims')


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

def fetch_gbif_vernacular_names(taxonomy: Taxonomy):
    if not taxonomy.gbif_key:
        return False
    vernacular_names = get_vernacular_names(taxonomy.gbif_key)
    logger.info('Fetching vernacular names for {}'.format(
        taxonomy.canonical_name
    ))
    if vernacular_names:
        logger.info('Found %s vernacular names' % len(
            vernacular_names['results']))
        order = 1
        for result in vernacular_names['results']:
            fields = {}
            source = result['source'] if 'source' in result else ''
            if 'language' in result:
                fields['language'] = result['language']
            if 'taxonKey' in result:
                fields['taxon_key'] = int(result['taxonKey'])
            fields['order'] = order

            vernacular_name, created = (
                VernacularName.objects.update_or_create(
                    name=result['vernacularName'],
                    source=source,
                    defaults=fields
                )
            )

            taxonomy.vernacular_names.add(vernacular_name)
            order += 1

        taxonomy.save()


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
        logger.debug("Skipping UNRANKED record – GBIF key %s", gbif_data.get("key"))
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

    if gbif_key:
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
        fetch_parent = not taxonomy.parent
        if taxonomy.parent and species_data and 'parentKey' in species_data:
            fetch_parent = taxonomy.parent.gbif_key != species_data['parentKey']
        if fetch_parent:
            # Get parent
            parent_taxonomy = None
            if 'parentKey' in species_data:
                parent_key = species_data['parentKey']
                log_info('Get parent with parentKey : %s' % parent_key)
                parent_taxonomy = fetch_all_species_from_gbif(
                    gbif_key=parent_key,
                    parent=None,
                    fetch_children=False
                )
            if parent_taxonomy:
                taxonomy.parent = parent_taxonomy
                taxonomy.save()

    max_tries = 10
    current_try = 0

    # Validate parents
    if taxonomy.rank.lower() == 'kingdom':
        taxon_parent = taxonomy
    else:
        taxon_parent = taxonomy.parent

    # Traverse up the hierarchy to find a 'kingdom' or reach max tries
    while current_try < max_tries and taxon_parent.parent and taxon_parent.rank.lower() != 'kingdom':
        taxon_parent = taxon_parent.parent
        current_try += 1

    # If a 'kingdom' was not found within max tries
    if taxon_parent.rank.lower() != 'kingdom' and current_try < max_tries:
        parent_key = taxon_parent.gbif_data.get('parentKey')
        if parent_key:
            parent_taxonomy = fetch_all_species_from_gbif(
                gbif_key=parent_key,
                parent=None,
                fetch_children=False
            )
            if parent_taxonomy:
                taxon_parent.parent = parent_taxonomy
                taxon_parent.save()

    # Check if there is an accepted key
    if (
        'acceptedKey' in species_data and
        'synonym' in species_data['taxonomicStatus'].lower().strip()
    ):
        accepted_taxonomy = fetch_all_species_from_gbif(
            gbif_key=species_data['acceptedKey'],
            taxonomic_rank=taxonomy.rank,
            parent=taxonomy.parent,
            fetch_children=False
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
