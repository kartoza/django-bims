import logging
import json
from django.db.models.fields.related import ForeignObjectRel
from django.db.models import Q, Min
from bims.utils.gbif import (
    get_children, find_species, get_species, get_vernacular_names,
    gbif_name_suggest
)
from bims.models import Taxonomy, VernacularName
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
        ).exclude(id=excluded_taxon.id)

    if taxa.count() < 1:
        return

    logger.info('Merging %s data' % len(taxa))

    links = [
        rel.get_accessor_name() for rel in excluded_taxon._meta.get_fields() if
        issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for taxon in taxa:
            logger.info('----- {} -----'.format(str(taxon)))
            for link in links:
                try:
                    objects = getattr(taxon, link).all()
                    if objects.count() > 0:
                        print('Updating {obj} for User : {user}'.format(
                            obj=str(objects.model._meta.label),
                            user=str(taxon)
                        ))
                        update_dict = {
                            getattr(taxon, link).field.name: excluded_taxon
                        }
                        objects.update(**update_dict)
                except Exception as e:  # noqa
                    continue
            logger.info(''.join(['-' for i in range(len(str(taxon)) + 12)]))

    taxa.delete()


def check_taxa_duplicates(taxon_name, taxon_rank):
    """
    Check for taxa duplicates, then merge if found
    :param taxon_name: Name of the taxon to check
    :param taxon_rank: Rank of the taxon to check
    :return: Merged taxonomy
    """
    taxon_rank = taxon_rank.strip().upper()
    taxon_name = taxon_name.strip()
    taxa = Taxonomy.objects.filter(
        Q(canonical_name__iexact=taxon_name) |
        Q(legacy_canonical_name__icontains=taxon_name),
        rank=taxon_rank
    )
    if not taxa.count() > 1:
        return
    preferred_taxa = taxa
    accepted_taxa = taxa.filter(taxonomic_status='ACCEPTED')
    if accepted_taxa.exists():
        preferred_taxa = accepted_taxa
    preferred_taxon = preferred_taxa.values('gbif_key', 'id').annotate(
        Min('gbif_key')).order_by('gbif_key')[0]
    preferred_taxon_gbif_data = get_species(preferred_taxon['gbif_key'])
    preferred_taxon = Taxonomy.objects.get(
        id=preferred_taxon['id']
    )
    for taxon in taxa[1:]:
        gbif_data = get_species(taxon.gbif_key)
        if not preferred_taxon_gbif_data:
            preferred_taxon = taxon
            preferred_taxon_gbif_data = gbif_data
            continue
        if not gbif_data:
            continue
        if gbif_data['taxonomicStatus'] == 'ACCEPTED':
            preferred_taxon_gbif_data = gbif_data
            preferred_taxon = taxon
            continue
        if 'issues' in gbif_data and len(gbif_data['issues']) > 0:
            continue
        if 'nubKey' not in gbif_data:
            continue
        if (
            'taxonomicStatus' in gbif_data and
            gbif_data['taxonomicStatus'] != 'ACCEPTED'
        ):
            continue
        if 'key' not in preferred_taxon_gbif_data:
            preferred_taxon = taxon
            preferred_taxon_gbif_data = gbif_data
            continue
        if (
            'key' in gbif_data and
            gbif_data['key'] > preferred_taxon_gbif_data['key']
        ):
            continue
        preferred_taxon = taxon
        preferred_taxon_gbif_data = gbif_data

    merge_taxa_data(
        taxa_list=taxa.exclude(id=preferred_taxon.id),
        excluded_taxon=preferred_taxon
    )
    return preferred_taxon


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
    if 'oldKey' in gbif_data:
        taxa = Taxonomy.objects.filter(
            gbif_key=gbif_data['oldKey']
        )
    if not taxa:
        taxa = Taxonomy.objects.filter(
            scientific_name=scientific_name,
            canonical_name=canonical_name,
            taxonomic_status=TaxonomicStatus[
                gbif_data['taxonomicStatus']].name,
            rank=rank,
        )
    if not taxa.exists():
        taxonomy = Taxonomy.objects.create(
            scientific_name=scientific_name,
            canonical_name=canonical_name,
            taxonomic_status=TaxonomicStatus[
                gbif_data['taxonomicStatus']].name,
            rank=rank,
        )
    else:
        taxa.update(
            scientific_name=scientific_name,
            canonical_name=canonical_name,
            taxonomic_status=TaxonomicStatus[
                gbif_data['taxonomicStatus']].name,
            rank=rank,
        )
        taxonomy = taxa[0]
    preferred_taxon = check_taxa_duplicates(taxonomy.canonical_name, rank)
    if preferred_taxon:
        taxonomy = preferred_taxon
    if 'authorship' in gbif_data:
        taxonomy.author = gbif_data['authorship']
    taxonomy.gbif_key = species_key
    taxonomy.gbif_data = gbif_data

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
    should_get_children=False,
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

    legacy_name = species_data['canonicalName']

    # Check if nubKey is identical with the key
    # if not then fetch the species with the nubKey to get a better data
    rank_key = None
    if taxonomic_rank:
        rank_key = '{}Key'.format(taxonomic_rank.lower())
    if 'nubKey' in species_data or rank_key:
        if gbif_key:
            temp_key = gbif_key
        else:
            temp_key = species_data['key']
        if 'nubKey' in species_data:
            nub_key = species_data['nubKey']
            if nub_key != temp_key:
                old_key = nub_key
                species_data = get_species(nub_key)
                species_data['oldKey'] = old_key
        else:
            if rank_key in species_data:
                old_key = species_data['key']
                if old_key != species_data[rank_key]:
                    species_data = get_species(species_data[rank_key])
                    species_data['oldKey'] = old_key

    # Check if there is accepted key
    if 'acceptedKey' in species_data:
        species_data = get_species(species_data['acceptedKey'])

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


def update_taxa_synonym(taxa_id):
    """
    Get the accepted data from synonym.
    :param taxa_id: id of the taxa
    :return: accepted taxa
    """
    logger.debug('Update taxon synonym')
    try:
        taxon = Taxonomy.objects.get(id=taxa_id)
    except Taxonomy.DoesNotExist:
        logger.info('Taxonomy not found')
        return None

    if taxon.taxonomic_status != 'SYNONYM':
        logger.debug('Taxon is not synonym')
        return None

    gbif_data = {}
    if taxon.gbif_data:
        gbif_data = json.loads(taxon.gbif_data)

    if 'acceptedKey' not in gbif_data:
        gbif_data = get_species(taxon.gbif_key)

    if 'acceptedKey' in gbif_data:
        key = gbif_data['acceptedKey']
        accepted_gbif_data = get_species(key)
        accepted_gbif_data['oldKey'] = taxon.gbif_key
        legacy_name = (
            taxon.legacy_canonical_name if
            taxon.legacy_canonical_name else
            taxon.canonical_name
        )
        accepted_taxonomy = create_or_update_taxonomy(accepted_gbif_data)
        check_taxa_duplicates(legacy_name, accepted_taxonomy.rank)
        return accepted_taxonomy
    else:
        logger.info('Could not found accepted taxon')
        return None


def check_taxon_parent(taxonomy):
    """
    Check if parent of the taxonomy is identical with one from gbif
    :param taxonomy: Taxonomy object
    :return: taxonomy
    """
    logger.debug('Check taxon parent')
    if not taxonomy.gbif_key:
        logger.debug('Gbif key not found')
        return
    gbif_data = get_species(taxonomy.gbif_key)

    parent_key_found = True
    fetch_parent = False

    if 'parentKey' not in gbif_data:
        logger.debug('Missing parent key')
        parent_key_found = False
        fetch_parent = True

    current_parent = taxonomy.parent
    if current_parent and parent_key_found:
        current_parent_gbif_key = current_parent.gbif_key
        if current_parent_gbif_key != int(gbif_data['parentKey']):
            fetch_parent = True
        else:
            logger.debug('Taxon parent is correct')

    if fetch_parent:
        if parent_key_found:
            logger.debug('Updating parent')
            parents = Taxonomy.objects.filter(gbif_key=gbif_data['parentKey'])
            if parents.exists():
                taxonomy.parent = parents[0]
            else:
                parent = fetch_all_species_from_gbif(
                    gbif_key=gbif_data['parentKey']
                )
                taxonomy.parent = parent
            taxonomy.save()
    return taxonomy
