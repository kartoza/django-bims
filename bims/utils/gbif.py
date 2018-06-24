# coding: utf-8
from requests.exceptions import HTTPError
from pygbif import species
from bims.models import Taxon


def update_taxa():
    """Get all taxon, then update the data bimsd on the gbif id.
    """
    taxa = Taxon.objects.all()
    if not taxa:
        print('No taxon found')
    for taxon in taxa:
        print('Update taxon for %s with gbif id %s' % (
            taxon.common_name, taxon.gbif_id
        ))
        try:
            response = species.name_usage(key=taxon.gbif_id)
            if response:
                if 'canonicalName' in response:
                    taxon.common_name = response['canonicalName']
                if 'scientificName' in response:
                    taxon.scientific_name = response['scientificName']
                if 'authorship' in response:
                    taxon.author = response['authorship']
                taxon.save()
                print('Taxon updated')
        except HTTPError as e:
            print('Taxon not updated')
            print(e)


def find_species(original_species_name):
    """
    Find species from gbif with lookup query.
    :param original_species_name: the name of species we want to find
    :return: List of species
    """
    print('Find species : %s' % original_species_name)
    list_of_species = []
    try:
        response = species.name_lookup(
            q=original_species_name,
            limit=3,
            offset=2
        )
        if 'results' in response:
            results = response['results']
            for result in results:
                if 'nubKey' in result:
                    list_of_species.append(result)
    except HTTPError:
        print('Species not found')

    return list_of_species


def update_fish_collection_record(fish_collection):
    """
    Update taxon for a fish collection.
    :param fish_collection: Fish collection record model
    """
    results = find_species(fish_collection.original_species_name)

    for result in results:
        if 'nubKey' in result:
            taxon, created = Taxon.objects.get_or_create(
                    gbif_id=result['nubKey'])
            if 'canonicalName' in result:
                taxon.common_name = result['canonicalName']
            if 'scientificName' in result:
                taxon.scientific_name = result['scientificName']
            if 'authorship' in result:
                taxon.author = result['authorship']
            taxon.save()
            fish_collection.taxon_gbif_id = taxon
            fish_collection.save()
            continue
