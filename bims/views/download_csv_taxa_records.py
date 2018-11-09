# coding=utf-8
import csv
from django.http import HttpResponse
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models.taxon import Taxon
from bims.api_views.collection import GetCollectionAbstract


def download_csv_site_taxa_records(request):
    taxon_id = request.GET.get('taxon')
    query_value = request.GET.get('search')
    filters = request.GET

    # Search collection
    collection_results, \
    site_results, \
    fuzzy_search = GetCollectionAbstract.apply_filter(
            query_value,
            filters,
            ignore_bbox=True)

    records = [q.object for q in collection_results]

    current_model = BiologicalCollectionRecord

    try:
        children_model = records[0].get_children()
        if children_model:
            current_model = children_model
    except:
        pass

    fields = [f.name for f in current_model._meta.get_fields()]
    fields.remove('ready_for_validation')
    fields.remove('validated')

    if 'biologicalcollectionrecord_ptr' in fields:
        fields.remove('biologicalcollectionrecord_ptr')

    taxon = Taxon.objects.get(pk=taxon_id)
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename="'+ taxon.common_name +'.csv"'

    writer = csv.writer(response)
    writer.writerow(['Taxon', taxon.common_name])
    writer.writerow(['Total records', len(records)])
    writer.writerow(['GBIF ID', taxon.gbif_id])
    writer.writerow([''])
    writer.writerow(fields + ['coordinates'])

    for record in records:
        try:
            children_record = record.get_children()
            if children_record:
                record = children_record
        except:
            pass
        row_object = []
        for field in fields:
            row_object.append(getattr(record, field))
        row_object.append('%s,%s' % (
            record.site.get_centroid().coords[1],
            record.site.get_centroid().coords[0],
        ))
        writer.writerow(row_object)

    return response
