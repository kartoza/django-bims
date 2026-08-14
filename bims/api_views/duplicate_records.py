import logging
from django.http import JsonResponse
from rest_framework.views import APIView
from bims.tasks.duplicate_records import download_duplicated_records_to_csv
from bims.helpers.get_duplicates import get_duplicate_records

logger = logging.getLogger('bims')


class DuplicateRecordsApiView(APIView):
    """Queue a download request for duplicate records.

    Instead of returning the CSV directly, this creates a ``DownloadRequest``
    and queues a background task that writes the file and attaches it to the
    request. Admins can then track the progress and download the file from the
    Download Requests page.
    """

    def post(self, request, *args):
        from django.contrib.sites.models import Site
        from bims.models.download_request import DownloadRequest

        user = request.user
        if not user.is_authenticated or not (
                user.is_staff or user.is_superuser):
            return JsonResponse({
                'status': 'failed',
                'message': 'You do not have permission to perform this action.'
            }, status=403)

        if not get_duplicate_records().exists():
            return JsonResponse({
                'status': 'failed',
                'message': 'No duplicated records'
            })

        download_request = DownloadRequest.objects.create(
            requester=user,
            resource_name='Duplicate Records',
            resource_type=DownloadRequest.CSV,
            request_category='Duplicate Records',
            processing=True,
            approved=True,
            source_site=Site.objects.get_current(),
        )

        download_duplicated_records_to_csv.delay(download_request.id)

        return JsonResponse({
            'status': 'processing',
            'download_request_id': download_request.id
        })
