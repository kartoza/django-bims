# coding=utf-8
import os
import errno
import sys
from django.conf import settings
from django.http import HttpResponse, Http404
from bims.models.taxonomy import Taxonomy
from bims.tasks.collection_record import download_data_to_csv


if sys.version_info[0] >= 3:
    unicode = str


def download_csv_site_taxa_records(request):
    taxon_id = request.GET.get('taxon')
    try:
        taxon = Taxonomy.objects.get(pk=taxon_id)
    except Taxonomy.DoesNotExist:
        raise Http404('Taxonomy does not exist')


    # Check if the file exists in the processed directory
    filename = '{name}.csv'.format(
        name=taxon.name
    )
    folder = settings.PROCESSED_CSV_PATH
    path_folder = os.path.join(settings.MEDIA_ROOT, folder)
    path_file = os.path.join(path_folder, filename)

    try:
        os.mkdir(path_folder)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass

    download_data_to_csv.delay(
        path_file,
        request.GET,
        send_email=False,
    )

    # Create the HttpResponse object with the appropriate CSV header.
    csv_file = open(path_file, 'rb')
    response = HttpResponse(content=csv_file)
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = (
        'attachment; filename="' + taxon.canonical_name + '.csv"'
    )
    return response
