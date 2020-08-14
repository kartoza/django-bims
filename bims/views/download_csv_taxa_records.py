# coding=utf-8
import csv
import sys
from django.http import HttpResponse
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models.taxonomy import Taxonomy
from bims.api_views.search import CollectionSearch


if sys.version_info[0] >= 3:
    unicode = str


def download_csv_site_taxa_records(request):
    taxon_id = request.GET.get('taxon')
    filters = request.GET
    search = CollectionSearch(filters)
    records = search.process_search()

    current_model = BiologicalCollectionRecord

    fields = [f.name for f in current_model._meta.get_fields()]
    fields.remove('ready_for_validation')
    fields.remove('validated')
    fields.remove('reference')
    fields.remove('reference_category')

    if 'biologicalcollectionrecord_ptr' in fields:
        fields.remove('biologicalcollectionrecord_ptr')

    taxon = Taxonomy.objects.get(pk=taxon_id)
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename="' + taxon.canonical_name + '.csv"'

    writer = csv.writer(response)
    writer.writerow(['Taxon', taxon.canonical_name])
    writer.writerow(['Total records', len(records)])
    writer.writerow(['GBIF ID', taxon.gbif_key])
    writer.writerow([''])
    writer.writerow(fields + ['coordinates'])

    for record in records:
        row_object = []
        for field in fields:
            try:
                record_data = getattr(record, field)
            except AttributeError:
                record_data = '-'
            row_object.append(record_data)
        row_object.append('%s,%s' % (
            record.site.get_centroid().coords[1],
            record.site.get_centroid().coords[0],
        ))
        writer.writerow([unicode(s).encode('utf-8') for s in row_object])

    return response
