# coding: utf-8
from requests.exceptions import HTTPError
from pygbif import species
from bims.models import Taxon, TaxonomyField


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
            limit=3,
            offset=2
        )
        if 'results' in response:
            results = response['results']
            for result in results:
                if 'nubKey' in result and 'taxonomicStatus' in result:
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
    result = find_species(collection.original_species_name)

    if not result:
        return

    taxon, created = Taxon.objects.get_or_create(
            gbif_id=result['nubKey'])
    update_taxonomy_fields(taxon, result)
    collection.taxon_gbif_id = taxon
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
                taxon.vernacular_names =  vernacular_names
        except AttributeError:
            continue

    taxon.save()
