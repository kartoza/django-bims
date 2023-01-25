import logging
import os
import errno
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from bims.tasks.duplicate_records import download_duplicated_records_to_csv
from bims.helpers.get_duplicates import get_duplicate_records

logger = logging.getLogger('bims')


class DuplicateRecordsApiView(APIView):
    """ Get Duplicate Records"""

    def get(self, request, *args):

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="download.csv"'

        duplicated_values = get_duplicate_records()

        if not duplicated_values:
            return JsonResponse({
                'status': 'failed',
                'message': 'Data is empty'
            })

        filename = 'duplicate_records_{}.csv'.format(
            datetime.now().date()
        )

        # Check if filename exists
        path_folder = os.path.join(settings.MEDIA_ROOT,
                                   settings.PROCESSED_CSV_PATH)
        path_file = os.path.join(path_folder, filename)

        try:
            os.mkdir(path_folder)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass

        if duplicated_values.count() > 1:
            download_duplicated_records_to_csv.delay(
                path_file,
                self.request.user.email
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
