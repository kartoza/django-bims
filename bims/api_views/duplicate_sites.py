import logging
from django.http import JsonResponse
from rest_framework.views import APIView
from bims.tasks.duplicate_sites import download_duplicated_sites_to_csv
from bims.helpers.get_duplicates import get_duplicate_sites

logger = logging.getLogger('bims')


class DuplicateSitesApiView(APIView):
    """Queue a download request for duplicate location sites.

    Mirrors the duplicate records download: a ``DownloadRequest`` is created
    and a background task writes the CSV and attaches it, so admins can track
    the progress and download the file from the Download Requests page.
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

        if not get_duplicate_sites().exists():
            return JsonResponse({
                'status': 'failed',
                'message': 'No duplicated sites'
            })

        download_request = DownloadRequest.objects.create(
            requester=user,
            resource_name='Duplicate Sites',
            resource_type=DownloadRequest.CSV,
            request_category='Duplicate Sites',
            processing=True,
            approved=True,
            source_site=Site.objects.get_current(),
        )

        download_duplicated_sites_to_csv.delay(download_request.id)

        return JsonResponse({
            'status': 'processing',
            'download_request_id': download_request.id
        })
