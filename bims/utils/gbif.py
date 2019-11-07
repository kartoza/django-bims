# coding: utf-8
import requests
from requests.exceptions import HTTPError
from pygbif import species
from bims.models import (
    Taxon,
    TaxonomyField
)
from bims.models.taxonomy import Taxonomy
from bims.models.vernacular_name import VernacularName
from bims.enums import TaxonomicRank, TaxonomicStatus


def update_taxa():
    """Get all taxon, then update the data bimsd on the gbif id."""
    taxa = Taxon.objects.all()
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
    except (HTTPError, KeyError) as e:
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
    except (HTTPError, KeyError) as e:
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


def find_species(original_species_name, rank=None, returns_all=False):
    """
    Find species from gbif with lookup query.
    :param original_species_name: the name of species we want to find
    :param rank: taxonomy rank
    :param returns_all: returns all response
    :return: List of species
    """
    print('Find species : %s' % original_species_name)
    try:
        response = species.name_lookup(
            q=original_species_name,
            limit=20,
            rank=rank,
            status='ACCEPTED'
        )
        if 'results' in response:
            results = response['results']
            if returns_all:
                return results
            for result in results:
                rank = result.get('rank', '')
                rank_key = rank.lower() + 'Key'
                key_found = (
                    'nubKey' in result or rank_key in result)
                if key_found and 'taxonomicStatus' in result:
                    if result['taxonomicStatus'] == 'ACCEPTED' or \
                        result['taxonomicStatus'] == 'SYNONYM':
                        return result
    except HTTPError:
        print('Species not found')

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

    taxonomy = process_taxon_identifier(taxon_key)
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
    taxon_fields = Taxon._meta.get_fields()
    for field in taxon_fields:
        if isinstance(field, TaxonomyField):
            if field.taxonomy_key in response:
                setattr(
                    taxon,
                    field.get_attname(),
                    response[field.taxonomy_key])
            continue

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


def process_taxon_identifier(key, fetch_parent=True, get_vernacular=True):
    """
    Get taxon detail
    :param key: gbif key
    :param fetch_parent: whether need to fetch parent, default to True
    :param get_vernacular: get vernacular names
    :return:
    """
    # Get taxon
    print('Get taxon identifier for key : %s' % key)

    try:
        taxon_identifier = Taxonomy.objects.get(
            gbif_key=key,
            scientific_name__isnull=False
        )
        if taxon_identifier.parent or taxon_identifier.rank == 'KINGDOM':
            return taxon_identifier
    except Taxonomy.DoesNotExist:
        pass

    detail = get_species(key)
    taxon_identifier = None

    try:
        print('Found detail for %s' % detail['scientificName'])
        taxon_identifier, status = Taxonomy.objects.get_or_create(
            gbif_key=detail['key'],
            scientific_name=detail['scientificName'],
            canonical_name=detail['canonicalName'],
            taxonomic_status=TaxonomicStatus[
                detail['taxonomicStatus']].name,
            rank=TaxonomicRank[
                detail['rank']].name,
        )
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
                    taxon_identifier.vernacular_names.add(vernacular_name)
                taxon_identifier.save()

        if 'parentKey' in detail and fetch_parent:
            print('Found parent')
            taxon_identifier.parent = process_taxon_identifier(
                detail['parentKey'],
                get_vernacular=get_vernacular
            )
            taxon_identifier.save()
    except (KeyError, TypeError) as e:
        print(e)
        pass

    return taxon_identifier


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
        species_detail = process_taxon_identifier(key, fetch_parent)

    return species_detail

import urllib
def suggest_search(query_params):
    """
    Search from gbif using suggestion api
    :param query_params: Query parameter
    :return: list of taxon
    """
    api_url = 'http://api.gbif.org/v1/species/suggest?{param}'.format(
        param=urllib.urlencode(query_params)
    )
    try:
        response = requests.get(api_url)
        results = response.json()
        return results
    except (HTTPError, KeyError) as e:
        print(e)
        return None
