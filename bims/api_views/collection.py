# coding=utf8

import json
from hashlib import md5
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
from bims.serializers.location_site_serializer import \
    LocationSiteClusterSerializer
from bims.utils.cluster_point import (
    within_bbox,
    overlapping_area,
    update_min_bbox
)
from bims.models.search_process import SearchProcess
from bims.utils.url import remove_params_from_uri
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

        not_needed_params = [
            'zoom',
            'bbox'
        ]

        search_uri = remove_params_from_uri(
            not_needed_params,
            search_uri
        )

        if queryset:
            query_count = queryset.count()
        else:
            query_count = site_queryset.count()

        today_date = datetime.date.today()

        if not site_id or site_id == '':
            filters = self.request.GET
            title = ''
            for key, value in filters.iteritems():
                if value and value != '' and value != [] and value != '[]':
                    filter_title = key + '=' + value + '-'
                    title += filter_title
            if title != '':
                title = title[:-1]
                filename = title + '.csv'
            else:
                filename = md5(
                    '%s%s%s' % (
                        search_uri,
                        query_count,
                        today_date)
                ).hexdigest()
                filename += '.csv'
        else:
            filename = site_id + '.csv'

        # Check if filename exists
        filename = '{}.csv'.format(md5(filename).hexdigest())
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


class ClusterCollection(GetCollectionAbstract):
    """
    Clustering collection with same taxon
    """

    @staticmethod
    def clustering_process(
            collection_records,
            site_records,
            zoom,
            pix_x,
            pix_y,
            cluster_points=[],
            sites=[]):
        """
        Iterate records and create point clusters
        We use a simple method that for every point, that is not within any
        cluster, calculate it's 'catchment' area and add it to the cluster
        If a point is within a cluster 'catchment' area increase point
        count for that cluster and recalculate clusters minimum bbox

        :param collection_records: collection records.
        :type collection_records: search query set

        :param site_records: site records.
        :type site_records: search query set

        :param zoom: zoom level of map
        :type zoom: int

        :param pix_x: pixel x of icon
        :type pix_x: int

        :param pix_y: pixel y of icon
        :type pix_y: int
        """
        for collection in GetCollectionAbstract.queryset_gen(
                collection_records):
            # get x,y of site
            try:
                x = collection.site.geometry_point.x
                y = collection.site.geometry_point.y
                location_site = collection.site
                if collection.site.id in sites:
                    continue
                sites.append(collection.site_id)
            except (ValueError, AttributeError):
                continue

            # check every point in cluster_points
            for pt in cluster_points:
                if 'minbbox' not in pt:
                    pt['minbbox'] = pt['bbox']

                if within_bbox((x, y), pt['minbbox']):
                    # it's in the cluster 'catchment' area
                    pt['count'] += 1
                    pt['minbbox'] = update_min_bbox(
                        (x, y), pt['minbbox'])
                    break

            else:
                # point is not in the catchment area of any cluster
                x_range, y_range = overlapping_area(
                    zoom, pix_x, pix_y, y)
                bbox = (
                    x - x_range * 1.5, y - y_range * 1.5,
                    x + x_range * 1.5, y + y_range * 1.5
                )
                serializer = LocationSiteClusterSerializer(
                    location_site)
                new_cluster = {
                    'count': 1,
                    'bbox': bbox,
                    'coordinates': [x, y],
                    'record': serializer.data
                }

                cluster_points.append(new_cluster)

        return cluster_points, sites

    def get(self, request, format=None):
        import hashlib
        import json
        from bims.tasks.cluster import generate_search_cluster

        # zoom = request.GET.get('zoom', None)
        # icon_pixel_x = request.GET.get('icon_pixel_x', None)
        # icon_pixel_y = request.GET.get('icon_pixel_y', None)
        query_value = request.GET.get('search')
        process = request.GET.get('process', None)
        filters = request.GET

        search_uri = request.build_absolute_uri()
        search_uri = remove_params_from_uri(
            ['zoom'],
            search_uri
        )

        search_processes = SearchProcess.objects.filter(
            category='cluster_generation',
            query=search_uri
        )

        if search_processes.exists():
            # There should not be more than 1 data
            if len(search_processes) > 1:
                for search_object in search_processes[1:len(search_processes)]:
                    search_object.delete()
            search_process = search_processes[0]
        else:
            search_process = SearchProcess.objects.create(
                category='cluster_generation',
                query=search_uri
            )

        if search_process.file_path:
            if os.path.exists(search_process.file_path):
                try:
                    raw_data = open(search_process.file_path)
                    return Response(json.load(raw_data))
                except ValueError:
                    pass
            else:
                search_process.finished = False
                search_process.save()

        # if not zoom or not icon_pixel_x or not icon_pixel_y:
        #     return HttpResponseBadRequest(
        #         'zoom, icon_pixel_x, and icon_pixel_y need to be '
        #         'in parameters. '
        #         'zoom : zoom level of map. '
        #         'icon_pixel_x: size x of icon in pixel. '
        #         'icon_pixel_y: size y of icon in pixel. ')
        if not process:
            collection_results, \
                site_results, \
                fuzzy_search = self.apply_filter(
                    query_value,
                    filters,
                    ignore_bbox=True)

            data_for_filename = dict()
            data_for_filename['search_uri'] = search_uri
            data_for_filename['collection_results_length'] = len(
                collection_results)
            data_for_filename['site_results_length'] = len(site_results)

            # Create filename from md5 of filters and results length
            filename = hashlib.md5(
                json.dumps(search_uri, sort_keys=True)
            ).hexdigest()
        else:
            filename = process

        search_process.process_id = filename
        search_process.save()

        # Check if filename exists
        folder = 'search_cluster'
        path_folder = os.path.join(settings.MEDIA_ROOT, folder)
        path_file = os.path.join(path_folder, filename)
        status = {
            'current_status': 'processing',
            'process': filename
        }

        if os.path.exists(path_file):
            raw_data = open(path_file)

            if raw_data:
                try:
                    json_data = json.load(raw_data)
                    return Response(json_data)
                except ValueError:
                    os.remove(path_file)
        else:
            try:
                os.mkdir(path_folder)
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
                pass

            generate_search_cluster.delay(
                query_value,
                filters,
                filename,
                path_file
            )

        return Response({
            'status': status
        })
