import logging
import os
import errno
from django.conf import settings
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from bims.models import BiologicalCollectionRecord
from bims.tasks.duplicate_records import download_duplicated_records_to_csv

logger = logging.getLogger('bims')


class DuplicateRecordsApiView(APIView):
    """ Get Duplicate Records"""

    def get(self, request, *args):

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="download.csv"'

        duplicated_values = BiologicalCollectionRecord.objects.values(
            'site_id', 'taxonomy_id', 'collection_date').annotate(
            duplicate=Count('*')
        ).exclude(duplicate=1)

        if not duplicated_values:
            return JsonResponse({
                'status': 'failed',
                'message': 'Data is empty'
            })

        filename = 'duplicated_records.csv'.encode('utf-8')

        # Check if filename exists
        folder = settings.PROCESSED_CSV_PATH
        path_folder = os.path.join(settings.MEDIA_ROOT, folder)
        path_file = os.path.join(path_folder, filename)

        try:
            os.mkdir(path_folder)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass

        if os.path.exists(path_file):
            return JsonResponse({
                'status': 'success',
                'filename': filename
            })

        if duplicated_values.count() > 1:
            download_duplicated_records_to_csv(
                duplicated_values,
                path_file
            )
        else:
            return JsonResponse({
                'status': 'failed',
                'message': 'No duplicated records'
            })

        return JsonResponse({
            'status': 'processing',
            'filename': filename
        })
