# coding: utf-8
import requests
import logging
import urllib
import simplejson
from requests.exceptions import HTTPError
from pygbif import species
from bims.models.taxonomy import Taxonomy
from bims.models.vernacular_name import VernacularName
from bims.enums import TaxonomicRank, TaxonomicStatus
from bims.utils.logger import log


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

            for result in response.get('results', []):
                if classifier:
                    classifier_found = True
                    for key, value in classifier.items():
                        if value:
                            classifier_found = False
                            key_db = 'class' if key == 'class_name' else key
                            if key_db in result and value.lower() == result[key_db].lower():
                                classifier_found = True
                    if not classifier_found:
                        continue

                rank = result.get('rank', '')
                rank_key = (rank.lower() + 'Key') if rank.lower() in RANK_KEYS else 'key'
                key_found = ('nubKey' in result or rank_key in result)

                if not key_found or 'taxonomicStatus' not in result:
                    continue

                status = result['taxonomicStatus']
                if status == 'ACCEPTED':
                    accepted_data = _prefer(result, accepted_data, original_species_name)
                    if accepted_data and 'nubKey' in accepted_data:
                        break

                elif status == 'SYNONYM':
                    synonym_data = _prefer(result, synonym_data, original_species_name)
                    if (accepted_data is None) and synonym_data and 'nubKey' in synonym_data:
                        break
                else:
                    other_data = _prefer(result, other_data, original_species_name)
                    if (accepted_data is None and synonym_data is None
                            and other_data and 'nubKey' in other_data):
                        break

        chosen = accepted_data or synonym_data or other_data
        if not chosen:
            return None
        nub_key = chosen.get('nubKey')
        if nub_key:
            canonical = get_species(nub_key)
            if canonical:
                return canonical
        return chosen
    except HTTPError:
        print('Species not found')
    except AttributeError:
        print('error')

    return None


def _prefer(candidate, current, original_name):
    """
    Pick the better of two GBIF lookup results:
    - Prefer an exact name match.
    - If both (or neither) match, keep the one with the smaller key.
    """
    if current is None:
        return candidate

    cand_name   = candidate.get('canonicalName') or candidate.get('scientificName', '')
    curr_name   = current.get('canonicalName')   or current.get('scientificName', '')
    cand_exact  = cand_name.lower() == original_name.lower()
    curr_exact  = curr_name.lower() == original_name.lower()

    if cand_exact and not curr_exact:
        return candidate
    if cand_exact == curr_exact:
        return candidate if candidate['key'] < current['key'] else current
    return current


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
    log('Get taxon for key : %s' % key)

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
    accepted_taxon = None

    # If synonym then get the accepted taxon
    if 'synonym' in detail['taxonomicStatus'].lower():
        accepted_taxon_key = detail.get('acceptedKey', '')
        if accepted_taxon_key:
            accepted_taxon = Taxonomy.objects.filter(
                gbif_key=accepted_taxon_key
            ).first()
            if not accepted_taxon:
                accepted_taxon = update_taxonomy_from_gbif(
                    accepted_taxon_key,
                    get_vernacular=get_vernacular
                )

    try:
        log('Found detail for %s' % detail['scientificName'])
        taxon, status = Taxonomy.objects.get_or_create(
            gbif_key=detail['key'],
            scientific_name=detail['scientificName'],
            canonical_name=detail['canonicalName'],
            taxonomic_status=TaxonomicStatus[
                detail['taxonomicStatus']].name,
            rank=TaxonomicRank[
                detail['rank']].name,
            author=detail.get('authorship', '')
        )
        taxon.gbif_data = detail
        if accepted_taxon:
            taxon.accepted_taxonomy = accepted_taxon
        taxon.save()

        # Get vernacular names
        if get_vernacular:
            vernacular_names = get_vernacular_names(detail['key'])
            if vernacular_names:
                log('Found %s vernacular names' % len(
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
    api_url = 'https://api.gbif.org/v1/species/suggest?{param}'.format(
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


def round_coordinates(coords):
    if isinstance(coords[0], list):
        return [round_coordinates(sub_coords) for sub_coords in coords]
    else:
        return [round(coord, 4) for coord in coords]
