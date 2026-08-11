# coding=utf-8
import os
import errno
from hashlib import sha256
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from bims.models.chemical_record import ChemicalRecord
from bims.serializers.chemical_records_serializer import (
    ChemicalRecordsOneRowSerializer)


class ChemicalRecordDownloader(APIView):

    def get(self, request):
        from bims.models.download_request import DownloadRequest
        from bims.tasks.chemical_record import download_chemical_data_to_csv

        site_id = request.GET.get('siteId', None)
        if not site_id:
            return JsonResponse({
                'status': 'failed',
                'message': 'Site ID is empty'
            })

        download_request_id = request.GET.get('downloadRequestId', '')
        try:
            download_request = DownloadRequest.objects.get(id=download_request_id)
        except DownloadRequest.DoesNotExist:
            return JsonResponse({
                'status': 'failed',
                'message': 'Download request does not exist'
            })

        query_string = 'chem_site_{}'.format(site_id)
        filename = sha256(query_string.encode('utf-8')).hexdigest() + '.csv'

        folder = settings.PROCESSED_CSV_PATH
        path_folder = os.path.join(
            settings.MEDIA_ROOT,
            folder,
            request.user.username
        )
        try:
            os.makedirs(path_folder, exist_ok=True)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

        path_file = os.path.join(path_folder, filename)

        if download_request.request_file and os.path.exists(
                str(download_request.request_file)):
            from bims.tasks.email_csv import send_csv_via_email
            send_csv_via_email.delay(
                user_id=request.user.id,
                csv_file=str(download_request.request_file),
                file_name='Physico-chemical Data',
                download_request_id=download_request_id
            )
            return JsonResponse({'status': 'processing'})

        if not download_request.approved:
            download_request.approved = True
            download_request.save(update_fields=['approved'])

        download_chemical_data_to_csv.delay(
            path_file,
            site_id,
            download_request_id=download_request_id,
            user_id=request.user.id,
        )

        return JsonResponse({'status': 'processing'})
