from datetime import datetime, timedelta

from django.contrib.sites.models import Site
from django.utils.timezone import make_aware
from preferences import preferences
import ast

from rest_framework import status

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
    """
    An API view for handling download requests. The view accepts POST requests
    with resource_name, resource_type, and purpose as required fields. It supports
    optional fields like dashboard_url, site_id, taxon_id, and notes. The view
    processes the download request and sends a notification email if the request
    is successful.
    """

    def post(self, request):
        """
        Handles the POST request for creating a new download request. Validates the
        input, creates the download request, and sends a notification email if
        successful.
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'User needs to be logged in first'},
                status=status.HTTP_401_UNAUTHORIZED)

        resource_name = request.POST.get('resource_name')
        resource_type = request.POST.get('resource_type')
        purpose = request.POST.get('purpose')
        dashboard_url = request.POST.get('dashboard_url', '')
        site_id = request.POST.get('site_id', '')
        taxon_id = request.POST.get('taxon_id', '')
        notes = request.POST.get('notes', '')
        auto_approved = ast.literal_eval(
            request.POST.get('auto_approved', 'False')
        )
        location_site = None
        taxon = None
        success = False

        approval_needed = (
            preferences.SiteSetting.enable_download_request_approval
        )

        if resource_type in ['CSV', 'PDF', 'XLS']:
            # Check unfinished big download tasks e.g. download occurrences or taxa list
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today - timedelta(days=5)
            start_date = make_aware(start_date)
            end_date = make_aware(today + timedelta(days=1))

            download_requests = DownloadRequest.objects.filter(
                resource_name__in=['Occurrence Data', 'Taxa List'],
                resource_type__in=['CSV', 'PDF', 'XLS'],
                requester=self.request.user,
                request_date__range=(start_date, end_date),
            )
            for download_request in download_requests:
                progress = download_request.progress
                try:
                    completed, total = progress.split('/')
                    completed = int(completed)
                    total = int(total)

                    if completed < total:
                        return Response(
                            {'error':
                                 'There are still ongoing download requests. '
                                 'Please wait for them to complete before trying again.'},
                            status=status.HTTP_401_UNAUTHORIZED)
                except ValueError:
                    continue

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
            notes=notes,
            source_site=Site.objects.get_current()
        )

        if not approval_needed or auto_approved:
            download_request.approved = True
            download_request.save()

        if download_request:
            send_new_csv_notification(
                download_request.requester,
                download_request.request_date,
                approval_needed
            )

        return Response({
            'success': success,
            'download_request_id': download_request.id
        })
