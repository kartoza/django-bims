# coding=utf-8
import os
from hashlib import sha256
import datetime
import errno
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.db.models import Q
from bims.models.chemical_record import ChemicalRecord
from bims.serializers.chemical_records_serializer import (
    ChemicalRecordsOneRowSerializer)


class ChemicalRecordDownloader(APIView):

    def convert_to_csv(self, queryset, ModelSerializer):
        """
        Converting data to csv.
        :param queryset: queryset that need to be converted
        :type queryset: QuerySet
        """
        from bims.tasks.chemical_record import download_chemical_data_to_csv

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="download.csv"'

        if not queryset:
            return JsonResponse({
                'status': 'failed',
                'message': 'Data is empty'
            })

        today_date = datetime.date.today()
        filename = sha256(
            'chem{}{}'.format(
                str(queryset.query),
                today_date).encode('utf-8')
        ).hexdigest()
        filename += '.csv'

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

        site_id = self.request.GET.get('siteId', None)
        if site_id:
            download_chemical_data_to_csv.delay(
                path_file,
                site_id,
            )
        else:
            return JsonResponse({
                'status': 'failed',
                'message': 'Site ID is empty'
            })

        return JsonResponse({
            'status': 'processing',
            'filename': filename
        })

    def get(self, request):
        site_id = request.GET.get('siteId', None)
        if site_id:
            collection_results = (
                ChemicalRecord.objects.filter(
                    Q(location_site_id=site_id) |
                    Q(survey__site_id=site_id)))
            return self.convert_to_csv(
                collection_results,
                ChemicalRecordsOneRowSerializer
            )
        else:
            return JsonResponse({
                'status': 'failed',
                'message': 'Site ID is empty'
            })
