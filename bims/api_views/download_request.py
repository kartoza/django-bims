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
        location_site = None
        success = False

        if not resource_name or not resource_type or not purpose:
            raise Http404('Missing required field.')

        if site_id:
            location_site = get_object_or_404(
                LocationSite,
                id=site_id
            )

        download_request_purpose = get_object_or_404(
            DownloadRequestPurpose,
            id=purpose
        )

        DownloadRequest.objects.get_or_create(
            resource_name=resource_name,
            resource_type=resource_type,
            purpose=download_request_purpose,
            requester=self.request.user,
            dashboard_url=dashboard_url,
            location_site=location_site
        )

        return Response({
            'success': success
        })
