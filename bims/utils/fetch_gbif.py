import logging
from bims.utils.gbif import (
    get_children, find_species, get_species, get_vernacular_names,
    gbif_name_suggest
)
from bims.models import Taxonomy, VernacularName, BiologicalCollectionRecord
from bims.enums import TaxonomicRank, TaxonomicStatus
from sass.models import SiteVisitBiotopeTaxon, SiteVisitTaxon

logger = logging.getLogger('bims')


def merge_taxa_data(gbif_key, excluded_taxon):
    """
    If there are more than one data with same gbif key,
    then merge those data
    """
    taxa = Taxonomy.objects.filter(
        gbif_key=gbif_key
    ).exclude(id=excluded_taxon.id)
    if len(taxa) <= 1:
        return

    logger.info('Merging %s data' % len(taxa))

    for taxon in taxa[1:]:
        BiologicalCollectionRecord.objects.filter(
            taxonomy=taxon
        ).update(
            taxonomy=excluded_taxon
        )
        SiteVisitTaxon.objects.filter(
            taxonomy=taxon
        ).update(
            taxonomy=excluded_taxon
        )
        SiteVisitBiotopeTaxon.objects.filter(
            taxon=taxon
        ).update(
            taxon=taxon
        )

    for taxon in taxa[1:]:
        taxon.delete()


def create_or_update_taxonomy(gbif_data, fetch_vernacular_names=True):
    """
    Create or update taxonomy data from gbif response data
    :param gbif_data: gbif response data
    :param fetch_vernacular_names: should fetch vernacular names
    """
    try:
        species_key = gbif_data['nubKey']
    except KeyError:
        species_key = gbif_data['key']
    try:
        rank = TaxonomicRank[gbif_data['rank']].name
    except KeyError:
        logger.error('No RANK')
        return None
    if 'scientificName' not in gbif_data:
        logger.error('No scientificName')
        return None
    if 'canonicalName' not in gbif_data:
        logger.error('No canonicalName')
        return None
    canonical_name = gbif_data['canonicalName']
    scientific_name = gbif_data['scientificName']
    taxa = Taxonomy.objects.filter(
        scientific_name=scientific_name,
        canonical_name=canonical_name,
        taxonomic_status=TaxonomicStatus[
            gbif_data['taxonomicStatus']].name,
        rank=rank,
    )
    if not taxa:
        taxonomy = Taxonomy.objects.create(
            scientific_name=scientific_name,
            canonical_name=canonical_name,
            taxonomic_status=TaxonomicStatus[
                gbif_data['taxonomicStatus']].name,
            rank=rank,
        )
    else:
        taxonomy = taxa[0]
    if 'authorship' in gbif_data:
        taxonomy.author = gbif_data['authorship']
    taxonomy.gbif_key = species_key
    taxonomy.gbif_data = gbif_data
    merge_taxa_data(species_key, taxonomy)

    if fetch_vernacular_names:
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
                try:
                    vernacular_name, status = (
                        VernacularName.objects.get_or_create(
                            name=result['vernacularName'],
                            **fields
                        ))
                except VernacularName.MultipleObjectsReturned:
                    vernacular_name = VernacularName.objects.filter(
                        name=result['vernacularName'],
                        **fields
                    )[0]
                taxonomy.vernacular_names.add(vernacular_name)
    taxonomy.save()
    return taxonomy


def fetch_all_species_from_gbif(
    species='',
    taxonomic_rank=None,
    gbif_key=None,
    parent=None,
    should_get_children=True,
    fetch_vernacular_names=False,
    use_name_lookup=True):
    """
    Get species detail and all species lower rank
    :param species: species name
    :param taxonomic_rank: taxonomy rank e.g. class
    :param gbif_key: gbif key
    :param parent: taxonomy parent
    :param should_get_children: fetch children or not
    :param fetch_vernacular_names: fetch vernacular names or not
    :param use_name_lookup: use name_lookup to search species
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
        if use_name_lookup:
            species_data = find_species(species, taxonomic_rank)
        else:
            species_data = gbif_name_suggest(
                q=species,
                rank=taxonomic_rank
            )

    # if species not found then return nothing
    if not species_data:
        logger.error('Species not found')
        return None

    # Check if nubKey same with the key
    # if not then fetch the species with the nubKey to get a better data
    if 'nubKey' in species_data:
        if gbif_key:
            temp_key = gbif_key
        else:
            temp_key = species_data['key']
        if species_data['nubKey'] != temp_key:
            species_data = get_species(species_data['nubKey'])

    logger.debug(species_data)
    if not species_data:
        return None
    taxonomy = create_or_update_taxonomy(species_data, fetch_vernacular_names)
    if not taxonomy:
        logger.error('Taxonomy not updated/created')
        return None
    species_key = taxonomy.gbif_key
    scientific_name = taxonomy.scientific_name

    if parent:
        taxonomy.parent = parent
        taxonomy.save()
    else:
        if not taxonomy.parent:
            # Get parent
            parent_taxonomy = None
            if 'parentKey' in species_data:
                parent_key = species_data['parentKey']
                logger.info('Get parent with parentKey : %s' % parent_key)
                parent_taxonomy = fetch_all_species_from_gbif(
                    gbif_key=parent_key,
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
        return taxonomy
