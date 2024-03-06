# coding: utf-8
import json
from typing import TextIO

import requests
import logging
import urllib
import simplejson
from django.contrib.gis.geos import GEOSGeometry
from requests.exceptions import HTTPError
from pygbif import species
from pygbif.occurrences import search
from bims.models.taxonomy import Taxonomy
from bims.models.vernacular_name import VernacularName
from bims.enums import TaxonomicRank, TaxonomicStatus
from bims.models.harvest_session import HarvestSession

logger = logging.getLogger(__name__)

RANK_KEYS = [
    'kingdom',
    'phylum',
    'class',
    'order',
    'family'
]


def update_taxa():
    """Get all taxon, then update the data based on the gbif id."""
    taxa = Taxonomy.objects.all()
    if not taxa:
        print('No taxon found')
    for taxon in taxa:
        print('Update taxon for %s with gbif id %s' % (
            taxon.common_name, taxon.gbif_id))
        try:
            response = species.name_usage(key=taxon.gbif_id)
            if response:
                update_taxonomy_fields(taxon, response)
                print('Taxon updated')
        except HTTPError as e:
            print('Taxon not updated')
            print(e)


def get_species(gbif_id):
    """
    Get species by gbif id
    :param gbif_id: gbif id
    :return: species dictionary
    """
    api_url = 'http://api.gbif.org/v1/species/' + str(gbif_id)
    try:
        response = requests.get(api_url)
        json_result = response.json()
        return json_result
    except (HTTPError, KeyError, simplejson.errors.JSONDecodeError) as e:
        print(e)
        return None


def get_vernacular_names(species_id):
    """
    Get vernacular names from species id
    :param species_id: taxonomy id
    :return: array of vernacular name
    """
    api_url = 'http://api.gbif.org/v1/species/%s/vernacularNames' % (
        str(species_id)
    )
    try:
        response = requests.get(api_url)
        json_result = response.json()
        return json_result
    except (HTTPError, KeyError, simplejson.errors.JSONDecodeError) as e:
        print(e)
        return None


def get_children(key):
    """
    Lists all direct child usages for a name usage
    :return: list of species
    """
    api_url = 'http://api.gbif.org/v1/species/{key}/children'.format(
        key=key
    )
    try:
        response = requests.get(api_url)
        json_response = response.json()
        if json_response['results']:
            return json_response['results']
        return None
    except (HTTPError, KeyError) as e:
        print(e)
        return None


def find_species(
        original_species_name,
        rank=None,
        returns_all=False,
        **classifier):
    """
    Find species from gbif with lookup query.
    :param original_species_name: the name of species we want to find
    :param rank: taxonomy rank
    :param returns_all: returns all response
    :param classifier: rank classifier
    :return: List of species
    """
    print('Find species : %s' % original_species_name)
    try:
        response = species.name_lookup(
            q=original_species_name,
            limit=50,
            rank=rank
        )
        accepted_data = None
        synonym_data = None
        other_data = None
        if 'results' in response:
            results = response['results']
            if returns_all:
                return results
            for result in results:
                if classifier:
                    classifier_found = True
                    for key, value in classifier.items():
                        if value:
                            classifier_found = False
                            if key == 'class_name':
                                key = 'class'
                            if key not in result:
                                continue
                            if value.lower() == result[key].lower():
                                classifier_found = True
                    if not classifier_found:
                        continue
                rank = result.get('rank', '')
                if rank.lower() in RANK_KEYS:
                    rank_key = rank.lower() + 'Key'
                else:
                    rank_key = 'key'
                key_found = (
                        'nubKey' in result or rank_key in result)
                if key_found and 'taxonomicStatus' in result:
                    taxon_name = ''
                    if 'canonicalName' in result:
                        taxon_name = result['canonicalName']
                    if not taxon_name and rank.lower() in result:
                        taxon_name = result[rank.lower()]
                    if not taxon_name and 'scientificName' in result:
                        taxon_name = result['scientificName']

                    if result['taxonomicStatus'] == 'ACCEPTED':
                        if accepted_data:
                            if taxon_name == original_species_name:
                                if result['key'] < accepted_data['key']:
                                    accepted_data = result
                        else:
                            accepted_data = result
                    if result['taxonomicStatus'] == 'SYNONYM':
                        if synonym_data:
                            if taxon_name == original_species_name:
                                if result['key'] < synonym_data['key']:
                                    synonym_data = result
                        else:
                            synonym_data = result
                    else:
                        if other_data:
                            if taxon_name == original_species_name:
                                if result['key'] < other_data['key']:
                                    other_data = result
                        else:
                            other_data = result
        if accepted_data:
            return accepted_data
        if synonym_data:
            return synonym_data
        return other_data
    except HTTPError:
        print('Species not found')
    except AttributeError:
        print('error')

    return None


def search_exact_match(species_name):
    """
    Search species detail
    :param species_name: species name
    :return: species detail if found
    """
    api_url = 'http://api.gbif.org/v1/species/match?name=' + str(species_name)
    try:
        response = requests.get(api_url)
        json_result = response.json()
        if json_result and 'usageKey' in json_result:
            key = json_result['usageKey']
            return key
        return None
    except (HTTPError, KeyError) as e:
        print(e)
        return None


def update_collection_record(collection):
    """
    Update taxon for a collection.
    :param collection: Biological collection record model
    """

    taxonomy = Taxonomy.objects.filter(
        scientific_name__contains=collection.original_species_name
    )
    if taxonomy:
        print('%s exists in Taxonomy' % collection.original_species_name)
        collection.taxonomy = taxonomy[0]
        collection.save()
        return

    result = find_species(collection.original_species_name)

    if not result:
        return

    if 'nubKey' in result:
        taxon_key = result['nubKey']
    elif 'speciesKey' in result:
        taxon_key = result['speciesKey']
    else:
        return

    taxonomy = update_taxonomy_from_gbif(taxon_key)
    collection.taxonomy = taxonomy
    collection.save()


def update_taxonomy_fields(taxon, response):
    """Helper to update taxonomy field of taxon from a response dictionary.

    :param taxon: The Taxon object.
    :type taxon: Taxon

    :param response: A dictionary contains of Taxonomy value.
    :type response: dict
    """
    # Iterate through all fields and update the one which is a
    # field from Taxonomy
    taxon_fields = Taxonomy._meta.get_fields()
    for field in taxon_fields:
        # Set vernacular names
        try:
            if field.get_attname() == 'vernacular_names':
                vernacular_names = []
                for vernacular_name in response['vernacularNames']:
                    if 'vernacularName' in vernacular_name:
                        vernacular_names.append(
                            vernacular_name['vernacularName']
                        )
                taxon.vernacular_names = vernacular_names
        except (AttributeError, KeyError) as e:
            print(e)
            continue

    taxon.save()


def update_taxonomy_from_gbif(key, fetch_parent=True, get_vernacular=True):
    """
    Update taxonomy data with data from gbif
    :param key: gbif key
    :param fetch_parent: whether need to fetch parent, default to True
    :param get_vernacular: get vernacular names
    :return:
    """
    # Get taxon
    print('Get taxon for key : %s' % key)

    try:
        taxon = Taxonomy.objects.get(
            gbif_key=key,
            scientific_name__isnull=False
        )
        if taxon.parent or taxon.rank == 'KINGDOM':
            return taxon
    except Taxonomy.DoesNotExist:
        pass

    detail = get_species(key)
    taxon = None

    try:
        print('Found detail for %s' % detail['scientificName'])
        taxon, status = Taxonomy.objects.get_or_create(
            gbif_key=detail['key'],
            scientific_name=detail['scientificName'],
            canonical_name=detail['canonicalName'],
            taxonomic_status=TaxonomicStatus[
                detail['taxonomicStatus']].name,
            rank=TaxonomicRank[
                detail['rank']].name,
        )
        taxon.gbif_data = detail
        taxon.save()

        # Get vernacular names
        if get_vernacular:
            vernacular_names = get_vernacular_names(detail['key'])
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
                    vernacular_name, status = (
                        VernacularName.objects.get_or_create(
                            name=result['vernacularName'],
                            **fields
                        )
                    )
                    taxon.vernacular_names.add(vernacular_name)
                taxon.save()

        if 'parentKey' in detail and fetch_parent:
            taxon.parent = update_taxonomy_from_gbif(
                detail['parentKey'],
                get_vernacular=get_vernacular
            )
            taxon.save()
    except (KeyError, TypeError) as e:
        print(e)
        pass

    return taxon


def search_taxon_identifier(search_query, fetch_parent=True):
    """
    Search from gbif api, then create taxon identifier
    :param search_query: string query
    :param fetch_parent: whether need to fetch parent, default to True
    :return:
    """
    print('Search for %s' % search_query)
    species_detail = None
    key = search_exact_match(search_query)

    if not key:
        species_detail = find_species(search_query)
        if not species_detail:
            return None
        rank = species_detail.get('rank', '')
        rank_key = rank.lower() + 'Key'

        if rank_key in species_detail:
            key = species_detail[rank_key]
        elif 'nubKey' in species_detail:
            key = species_detail['nubKey']

    if key:
        species_detail = update_taxonomy_from_gbif(key, fetch_parent)

    return species_detail


def suggest_search(query_params):
    """
    Search from gbif using suggestion api
    :param query_params: Query parameter
    :return: list of taxon
    """
    api_url = 'http://api.gbif.org/v1/species/suggest?{param}'.format(
        param=urllib.parse.urlencode(query_params)
    )
    try:
        response = requests.get(api_url)
        results = response.json()
        return results
    except (HTTPError, KeyError) as e:
        print(e)
        return None


def gbif_name_suggest(**kwargs):
    # Wrapper for pygbif name_suggest function
    response = species.name_suggest(**kwargs)
    if len(response) == 0:
        return None
    accepted_data = None
    synonym_data = None
    other_data = None
    for result in response:
        rank = result.get('rank', '')
        if rank.lower() in RANK_KEYS:
            rank_key = rank.lower() + 'Key'
        else:
            rank_key = 'key'
        key_found = (
                'nubKey' in result or rank_key in result)
        if key_found and 'status' in result:
            if result['status'] == 'ACCEPTED':
                if accepted_data:
                    if result['key'] < accepted_data['key']:
                        accepted_data = result
                else:
                    accepted_data = result
            if result['status'] == 'SYNONYM':
                if synonym_data:
                    if result['key'] < synonym_data['key']:
                        synonym_data = result
                else:
                    synonym_data = result
            else:
                if other_data:
                    if result['key'] < other_data['key']:
                        other_data = result
                else:
                    other_data = result
    if accepted_data:
        return accepted_data
    if synonym_data:
        return synonym_data
    return other_data


ACCEPTED_TAXON_KEY = 'acceptedTaxonKey'


def find_species_by_area(
        boundary_id,
        class_key=None,
        phylum_key=None,
        kingdom_key=None,
        max_limit=100,
        harvest_session: HarvestSession = None,
        validated=True
):
    """
    Searches for species within a specific area defined by a boundary, filtered by taxonomic keys.

    Parameters:
    boundary_id (int): The ID of the boundary within which to search for species.
    class_key (int, optional): The taxonomic class key for filtering species.
    phylum_key (int, optional): The taxonomic phylum key for filtering species.
    kingdom_key (int, optional): The taxonomic kingdom key for filtering species.
    max_limit (int, optional): The maximum number of species to be fetched.
    validated (bool, optional): Automatically validated the species

    Returns:
    list: A list of species found within the area, filtered by the provided taxonomic keys.
    """
    from bims.models.boundary import Boundary
    from bims.models.taxon_group_taxonomy import TaxonGroupTaxonomy
    from bims.models.taxon_group import TaxonGroup
    from bims.utils.fetch_gbif import fetch_all_species_from_gbif

    add_parent = True
    taxon_group = None
    log_file_path = None

    if harvest_session:
        taxon_group = harvest_session.module_group
        log_file_path = (
            harvest_session.log_file.path
            if harvest_session.log_file else None
        )

    def log_info(message: str):
        logger.info(message)
        if log_file_path:
            with open(log_file_path, 'a') as log_file:
                log_file.write('{}\n'.format(message))

    def is_canceled():
        if harvest_session:
            return HarvestSession.objects.get(
                id=harvest_session.id
            ).canceled
        return False

    def round_coordinates(coords):
        if isinstance(coords[0], list):
            return [round_coordinates(sub_coords) for sub_coords in coords]
        else:
            return [round(coord, 4) for coord in coords]

    def add_parent_to_group(taxon: Taxonomy, group: TaxonGroup):
        if taxon.parent:
            _taxon_group_taxonomy, _ = (
                TaxonGroupTaxonomy.objects.get_or_create(
                    taxongroup=group,
                    taxonomy=taxon,
                )
            )
            _taxon_group_taxonomy.is_validated = validated
            _taxon_group_taxonomy.save()
            add_parent_to_group(taxon.parent, group)
        else:
            return

    # Fetch the most recent boundary and its geometry
    geometry_str = ''
    try:
        boundary = Boundary.objects.get(id=boundary_id)
        geometry = boundary.geometry
        if not geometry:
            raise ValueError("No geometry found for the boundary.")
        geojson = json.loads(geometry.geojson)
        geojson['coordinates'] = round_coordinates(geojson['coordinates'])
        geometry_rounded = GEOSGeometry(json.dumps(geojson))
        geometry_str = str(geometry_rounded.ogr)

    except Boundary.DoesNotExist:
        logger.error(f"Boundary with ID {boundary_id} does not exist.")
        return []
    except Exception as e:
        logger.error(f"Error fetching boundary: {e}")
        return []

    species_keys = set()
    species_found = []

    def fetch_occurrences_by_area():
        offset = 0
        while True:
            if is_canceled():
                break
            try:
                occurrences_data = search(
                    geometry=geometry_str,
                    offset=offset,
                    classKey=class_key,
                    phylumKey=phylum_key,
                    kingdomKey=kingdom_key
                )
            except Exception as e:
                log_info(f"Error fetching occurrences data: {e}")
                break

            new_keys = {
                occurrence.get(ACCEPTED_TAXON_KEY) for occurrence in occurrences_data['results']}
            species_keys.update(new_keys)

            _max_limit = max_limit

            if not _max_limit:
                if 'count' in occurrences_data:
                    _max_limit = occurrences_data['count']
                else:
                    _max_limit = 99999

            log_info(f"Fetching occurrences data: {offset + occurrences_data['limit']}/{_max_limit}")

            log_info(f"Species found so far: {len(species_keys)}")
            if occurrences_data['endOfRecords'] or offset >= _max_limit or is_canceled():
                break

            offset += occurrences_data['limit']

    fetch_occurrences_by_area()

    log_info(f"Species found: {len(species_keys)}")

    for species_key in species_keys:
        if is_canceled():
            return species_found
        try:
            log_info('Processing {}'.format(species_key))
            taxonomy = fetch_all_species_from_gbif(
                gbif_key=species_key,
                fetch_children=False,
                log_file_path=log_file_path,
                fetch_vernacular_names=True
            )
            if taxonomy:
                log_info("Species added/updated : {}".format(
                    taxonomy.scientific_name
                ))
                species_found.append(taxonomy)
                if taxon_group:
                    taxon_group_taxonomy, created = (
                        TaxonGroupTaxonomy.objects.get_or_create(
                            taxongroup=taxon_group,
                            taxonomy=taxonomy,
                        )
                    )
                    taxon_group_taxonomy.is_validated = validated
                    taxon_group_taxonomy.save()

                    if add_parent:
                        add_parent_to_group(
                            taxonomy, taxon_group
                        )
        except Exception as e:
            log_info(f"Error fetching data for species key {species_key}: {e}")

    return species_found
