import logging
from bims.utils.gbif import (
    get_children, find_species, get_species, get_vernacular_names
)
from bims.models import Taxonomy, VernacularName
from bims.enums import TaxonomicRank, TaxonomicStatus

logger = logging.getLogger('bims')


def create_or_update_taxonomy(gbif_data):
    """
    Create or update taxonomy data from gbif response data
    :param gbif_data: gbif response data
    """
    try:
        species_key = gbif_data['nubKey']
    except KeyError:
        species_key = gbif_data['key']
    scientific_name = gbif_data['scientificName']
    try:
        rank = TaxonomicRank[gbif_data['rank']].name
    except KeyError:
        rank = TaxonomicRank.SPECIES.name
    taxa = Taxonomy.objects.filter(
        scientific_name=scientific_name,
        canonical_name=gbif_data['canonicalName'],
        taxonomic_status=TaxonomicStatus[
            gbif_data['taxonomicStatus']].name,
        rank=rank,
    )
    if not taxa:
        taxonomy = Taxonomy.objects.create(
            scientific_name=scientific_name,
            canonical_name=gbif_data['canonicalName'],
            taxonomic_status=TaxonomicStatus[
                gbif_data['taxonomicStatus']].name,
            rank=rank,
        )
    else:
        taxonomy = taxa[0]
    taxonomy.gbif_key = species_key
    vernacular_names = get_vernacular_names(species_key)
    if vernacular_names:
        print('Found %s vernacular names' % len(
            vernacular_names['results']))
        for result in vernacular_names['results']:
            fields = {}
            if 'source' in result:
                fields['source'] = result['source']
            if 'language' in result:
                fields['language'] = result['language']
            if 'taxonKey' in result:
                fields['taxon_key'] = int(result['taxonKey'])
            vernacular_name, status = VernacularName.objects.get_or_create(
                name=result['vernacularName'],
                **fields
            )
            taxonomy.vernacular_names.add(vernacular_name)
    taxonomy.save()
    return taxonomy


def fetch_all_species_from_gbif(
    species='',
    taxonomic_rank=None,
    gbif_key=None,
    parent=None,
    should_get_children=True):
    """
    Get species detail and all species lower rank
    :param species: species name
    :param taxonomic_rank: taxonomy rank e.g. class
    :param gbif_key: gbif key
    :param parent: taxonomy parent
    :param should_get_children: fetch children or not
    :return:
    """
    if gbif_key:
        logger.info('Get species {gbif_key}'.format(
            gbif_key=gbif_key
        ))
        species_data = get_species(gbif_key)
    else:
        logger.info('Fetching {species} - {rank}'.format(
            species=species,
            rank=taxonomic_rank
        ))
        species_data = find_species(species, taxonomic_rank)
    logger.debug(species_data)
    if not species_data:
        return None
    taxonomy = create_or_update_taxonomy(species_data)
    species_key = taxonomy.gbif_key
    scientific_name = taxonomy.scientific_name

    if parent:
        taxonomy.parent = parent
        taxonomy.save()
    else:
        # Get parent
        parent_taxonomy = None
        if 'parentKey' in species_data:
            parent_taxonomy = fetch_all_species_from_gbif(
                gbif_key=species_data['parentKey'],
                parent=None,
                should_get_children=False
            )
        if parent_taxonomy:
            taxonomy.parent = parent_taxonomy
            taxonomy.save()

    if not should_get_children:
        return taxonomy

    if species_key and scientific_name:
        logger.info('Get children from : {}'.format(species_key))
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
