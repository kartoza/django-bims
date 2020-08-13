# coding=utf8

import json
from hashlib import sha256
import datetime
import os
import errno
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.serializers.bio_collection_serializer import (
    BioCollectionOneRowSerializer,
    BioCollectionGeojsonSerializer
)
from bims.api_views.search import Search


class GetCollectionAbstract(APIView):
    """
    Abstract class for getting collection
    """

    @staticmethod
    def queryset_gen(sqs, exlude_ids=[]):
        """Return queryset from sqs"""
        for item in sqs:
            if item.id not in exlude_ids:
                yield item.object

    @staticmethod
    def is_using_filters(filters):
        taxon = filters.get('taxon', None)
        query_collector = filters.get('collector', None)
        boundary = filters.get('boundary', None)
        user_boundary = filters.get('userBoundary', None)
        query_category = filters.get('category', None)
        reference_category = filters.get('referenceCategory', None)
        reference = filters.get('reference', None)
        year_from = filters.get('yearFrom', None)
        year_to = filters.get('yearTo', None)
        months = filters.get('months', None)

        return bool(taxon or query_collector or
                    boundary or user_boundary or
                    query_category or reference_category or
                    year_from or year_to or months or reference)

    @staticmethod
    def get_all_validated():
        """
        Get all validated collection data
        :return: list of validated collection
        """
        return []

    @staticmethod
    def apply_filter(query_value, filters, ignore_bbox=False, only_site=False):
        """
        Apply filter and do the search to biological collection
        record and location site

        :param query_value: str
        :param filters: dict
        :param ignore_bbox: bool
        :returns:
        - collection_results : results from bio collection record
        - site_results : results from location site
        - fuzzy_search : if results from search is fuzzy search
        """
        collection_results = []
        site_results = []
        fuzzy_search = False
        return collection_results, site_results, fuzzy_search

    @staticmethod
    def combine_search_query_results(sqs_result_1, sqs_result_2):
        """
        Combine two search query results
        :param sqs_result_1: SQS
        :param sqs_result_2: SQS
        :return: combined search query results
        """
        if len(sqs_result_1) == 0 and len(sqs_result_2) == 0:
            return sqs_result_1

        if len(sqs_result_1) == 0:
            return sqs_result_2

        if len(sqs_result_2) == 0:
            return sqs_result_1

        if len(sqs_result_1) > len(sqs_result_2):
            return sqs_result_1 | sqs_result_2
        else:
            return sqs_result_2 | sqs_result_1


class CollectionDownloader(GetCollectionAbstract):
    """
    Download all collections with format
    """

    def convert_to_cvs(self, queryset, site_queryset, ModelSerializer):
        """
        Converting data to csv.
        :param queryset: queryset that need to be converted
        :type queryset: QuerySet
        """
        from bims.tasks.collection_record import download_data_to_csv

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="download.csv"'

        if not queryset and not site_queryset:
            return JsonResponse({
                'status': 'failed',
                'message': 'Data is empty'
            })

        # Filename
        site_id = self.request.GET.get('siteId')
        search_uri = self.request.build_absolute_uri()

        if queryset:
            query_count = queryset.count()
        else:
            query_count = site_queryset.count()

        today_date = datetime.date.today()

        if not site_id or site_id == '':
            filters = self.request.GET
            title = ''
            for key, value in filters.items():
                if value and value != '' and value != [] and value != '[]':
                    filter_title = key + '=' + value + '-'
                    title += filter_title
            if title != '':
                title = title[:-1]
                filename = title + '.csv'
            else:
                filename = sha256(
                    '%s%s%s' % (
                        search_uri,
                        query_count,
                        today_date).encode('utf-8')
                ).hexdigest()
                filename += '.csv'
        else:
            filename = site_id + '.csv'

        # Check if filename exists
        filename = '{}.csv'.format(sha256(
            filename.encode('utf-8')).hexdigest())
        folder = 'csv_processed'
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

        download_data_to_csv.delay(
            path_file,
            self.request.GET,
        )

        return JsonResponse({
            'status': 'processing',
            'filename': filename
        })

    def convert_to_geojson(self, queryset, Model, ModelSerializer):
        """
        Converting data to geojson.
        :param queryset: queryset that need to be converted
        :type queryset: QuerySet
        """
        serializer = ModelSerializer(
            queryset, many=True)
        response = HttpResponse(
            content=json.dumps(serializer.data),
            content_type='text/geojson')
        response['Content-Disposition'] = \
            'attachment; filename="download.geojson"'
        return response

    def get(self, request):
        filters = request.GET
        search = Search(filters)
        file_type = request.GET.get('fileType', None)
        if not file_type:
            file_type = 'csv'
        site_results = None

        collection_results = search.process_search()

        if file_type == 'csv':
            return self.convert_to_cvs(
                collection_results,
                site_results,
                BioCollectionOneRowSerializer)
        elif file_type == 'geojson':
            return self.convert_to_geojson(
                collection_results,
                BiologicalCollectionRecord,
                BioCollectionGeojsonSerializer)
        else:
            return Response([])
