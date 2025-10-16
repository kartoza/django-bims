from datetime import timedelta

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from preferences import preferences

from bims.download.csv_download import send_new_csv_notification
from bims.models.taxonomy import Taxonomy
from bims.models.location_site import LocationSite
from bims.models.download_request import DownloadRequest, DownloadRequestPurpose


@method_decorator(csrf_protect, name='dispatch')
class DownloadRequestApi(APIView):
    """
    Create a download request.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        data = request.data  # supports form or JSON

        resource_name = (data.get('resource_name') or '').strip()
        resource_type = (data.get('resource_type') or '').strip().upper()
        purpose_id = data.get('purpose')
        dashboard_url = data.get('dashboard_url', '')
        site_id = data.get('site_id') or ''
        taxon_id = data.get('taxon_id') or ''
        notes = data.get('notes', '')
        email = data.get('download_email', '')

        requested_auto = str(data.get('auto_approved', 'false')).lower() in ('1', 'true', 'yes')
        auto_approved = requested_auto and request.user.is_authenticated and request.user.is_staff

        ALLOWED_TYPES = {'CSV', 'PDF', 'XLS'}
        if resource_type and resource_type not in ALLOWED_TYPES:
            return Response({'error': 'Invalid resource_type.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_to_download = request.user.is_authenticated
        if not allowed_to_download and resource_name.lower() == 'taxa list' and preferences.SiteSetting.is_public_taxa:
            allowed_to_download = True

        if not allowed_to_download:
            return Response(
                {'error': 'User needs to be logged in first'}, status=status.HTTP_401_UNAUTHORIZED)

        if not resource_name or not resource_type or not purpose_id:
            return Response(
                {'error': 'Missing required field(s).'}, status=status.HTTP_400_BAD_REQUEST)

        location_site = None
        taxon = None
        if site_id:
            location_site = get_object_or_404(LocationSite, id=site_id)
        if taxon_id:
            taxon = get_object_or_404(Taxonomy, id=taxon_id)

        download_request_purpose = get_object_or_404(DownloadRequestPurpose, id=purpose_id)

        requester = request.user if request.user.is_authenticated else None

        if resource_type in ALLOWED_TYPES:
            end_date = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            start_date = end_date - timedelta(days=5)
            pending = DownloadRequest.objects.filter(
                resource_name__in=['Occurrence Data', 'Taxa List'],
                resource_type__in=['CSV', 'PDF', 'XLS'],
                requester=request.user if requester else None,
                request_date__range=(start_date, end_date),
            )
            for dr in pending:
                progress = (dr.progress or '').strip()
                if '/' in progress:
                    try:
                        completed_s, total_s = progress.split('/', 1)
                        if int(completed_s) < int(total_s):
                            return Response(
                                {
                                    'error': 'There are ongoing download requests. Please wait for them to finish.'
                                },
                                status=status.HTTP_429_TOO_MANY_REQUESTS
                            )
                    except ValueError:
                        pass

        approval_needed = preferences.SiteSetting.enable_download_request_approval

        download_request, created = DownloadRequest.objects.get_or_create(
            email=email,
            resource_name=resource_name,
            resource_type=resource_type,
            purpose=download_request_purpose,
            requester=requester,
            dashboard_url=dashboard_url,
            location_site=location_site,
            taxon=taxon,
            notes=notes,
            request_date=timezone.now()
        )

        if not approval_needed or auto_approved:
            download_request.approved = True
            download_request.save(update_fields=['approved'])

        send_new_csv_notification(
            download_request.requester,
            download_request.request_date,
            approval_needed,
            download_request.email
        )

        return Response({
            'success': True,
            'download_request_id': download_request.id
        })
