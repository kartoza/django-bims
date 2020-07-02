# coding=utf-8
import csv
from django.http import HttpResponse
from bims.models.taxon_group import TaxonGroup


def download_csv_taxa_list(request):
    taxon_group_id = request.GET.get('taxonGroup')
    taxon_name = request.GET.get('taxon', '')
    taxon_group = TaxonGroup.objects.get(
        id=taxon_group_id
    )
    taxa_list = taxon_group.taxonomies.all()
    if taxon_name:
        taxa_list = taxa_list.filter(
            canonical_name__icontains=taxon_name
        )

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename="' + taxon_group.name + '.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Taxon rank',
        'Kingdom',
        'Phylum',
        'Class',
        'Order',
        'Genus',
        'Species',
        'Taxon',
        'Scientific name and authority',
        'Common name',
        'Origin',
        'Endemism',
        'Conservation status'
    ])

    for taxon in taxa_list:
        row_object = list()
        vernacular_names = taxon.vernacular_names.all()
        row_object.append(
            taxon.rank
        )
        row_object.append(
            taxon.kingdom_name
        )
        row_object.append(
            taxon.phylum_name
        )
        row_object.append(
            taxon.class_name
        )
        row_object.append(
            taxon.order_name
        )
        row_object.append(
            taxon.genus_name
        )
        row_object.append(
            taxon.species_name
        )
        row_object.append(
            taxon.canonical_name
        )
        row_object.append(
            taxon.scientific_name
        )
        row_object.append(
            vernacular_names[0] if vernacular_names else '-'
        )
        row_object.append(
            taxon.origin
        )
        row_object.append(
            taxon.endemism.name if taxon.endemism else '-'
        )
        row_object.append(
            taxon.iucn_status.category if taxon.iucn_status else '-'
        )
        writer.writerow(row_object)

    return response
