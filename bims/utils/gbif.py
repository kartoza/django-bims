# coding: utf-8
import requests
from requests.exceptions import HTTPError
from pygbif import species
from bims.models import (
    Taxon,
    TaxonomyField
)
from bims.models.taxonomy import Taxonomy
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


def find_species(original_species_name):
    """
    Find species from gbif with lookup query.
    :param original_species_name: the name of species we want to find
    :return: List of species
    """
    print('Find species : %s' % original_species_name)
    try:
        response = species.name_lookup(
            q=original_species_name,
            limit=5
        )
        if 'results' in response:
            results = response['results']
            for result in results:
                key_found = 'nubKey' in result or 'speciesKey' in result
                if key_found and 'taxonomicStatus' in result:
                    if result['taxonomicStatus'] == 'ACCEPTED' or \
                            result['taxonomicStatus'] == 'SYNONYM':
                        return result
    except HTTPError:
        print('Species not found')

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


def process_taxon_identifier(key, fetch_parent=True):
    """
    Get taxon detail
    :param key: gbif key
    :param fetch_parent: whether need to fetch parent, default to True
    :return:
    """
    # Get taxon
    print('Get taxon identifier for key : %s' % key)

    try:
        taxon_identifier = Taxonomy.objects.get(
            gbif_key=key,
            scientific_name__isnull=False
        )
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
        if 'vernacularName' in detail:
            vernacular_names = detail['vernacularName'].split(',')
            taxon_identifier.vernacular_names = vernacular_names
            taxon_identifier.save()

        if 'parentKey' in detail and fetch_parent:
            print('Found parent')
            taxon_identifier.parent = process_taxon_identifier(
                detail['parentKey']
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
    species_detail = find_species(search_query)

    key = None
    if 'nubKey' in species_detail:
        key = species_detail['nubKey']
    elif 'speciesKey' in species_detail:
        key = species_detail['speciesKey']

    if key:
        species_detail = process_taxon_identifier(key, fetch_parent)

    return species_detail
