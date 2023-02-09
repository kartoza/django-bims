from bims.download.csv_download import send_new_csv_notification
from bims.models.taxonomy import Taxonomy

from bims.models.location_site import LocationSite
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response

from bims.models.download_request import (
    DownloadRequest,
    DownloadRequestPurpose
)


class DownloadRequestApi(APIView):

    def post(self, request):
        resource_name = request.POST.get('resource_name')
        resource_type = request.POST.get('resource_type')
        purpose = request.POST.get('purpose')
        dashboard_url = request.POST.get('dashboard_url', '')
        site_id = request.POST.get('site_id', '')
        taxon_id = request.POST.get('taxon_id', '')
        notes = request.POST.get('notes', '')
        location_site = None
        taxon = None
        success = False

        if not resource_name or not resource_type or not purpose:
            raise Http404('Missing required field.')

        if site_id:
            location_site = get_object_or_404(
                LocationSite,
                id=site_id
            )

        if taxon_id:
            taxon = get_object_or_404(
                Taxonomy,
                id=taxon_id
            )

        download_request_purpose = get_object_or_404(
            DownloadRequestPurpose,
            id=purpose
        )

        requester = (
            self.request.user if not self.request.user.is_anonymous else None
        )

        download_request, created = DownloadRequest.objects.get_or_create(
            resource_name=resource_name,
            resource_type=resource_type,
            purpose=download_request_purpose,
            requester=requester,
            dashboard_url=dashboard_url,
            location_site=location_site,
            taxon=taxon,
            notes=notes
        )

        if download_request.id and not download_request.request_file:
            send_new_csv_notification(
                download_request.requester,
                download_request.request_date
            )

        return Response({
            'success': success,
            'download_request_id': download_request.id
        })
