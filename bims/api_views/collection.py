# coding=utf8

import json
from hashlib import md5
import datetime
import os
import errno
from haystack.query import SearchQuerySet, SQ
from django.contrib.gis.geos import MultiPoint, Point
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models.taxon import Taxon
from bims.serializers.bio_collection_serializer import (
    BioCollectionSerializer,
    BioCollectionOneRowSerializer,
    BioCollectionGeojsonSerializer
)
from bims.utils.cluster_point import (
    within_bbox,
    overlapping_area,
    update_min_bbox,
    geo_serializer
)


class GetCollectionAbstract(APIView):
    """
    Abstract class for getting collection
    """

    @staticmethod
    def apply_filter(request, ignore_bbox=False):
        # get records with same taxon
        try:
            request_data = request.GET
        except AttributeError:
            request_data = request

        sqs = SearchQuerySet()

        query_value = request_data.get('search')
        if query_value:
            clean_query = sqs.query.clean(query_value)
            settings.ELASTIC_MIN_SCORE = 1.5
            results = sqs.filter(
                SQ(original_species_name=clean_query) |
                SQ(taxon_common_name__contains=clean_query) |
                SQ(taxon_scientific_name__contains=clean_query)
            ).models(BiologicalCollectionRecord, Taxon).order_by('-_score')
        else:
            settings.ELASTIC_MIN_SCORE = 0
            results = sqs.all().models(BiologicalCollectionRecord)

        taxon = request_data.get('taxon', None)
        if taxon:
            results = sqs.filter(
                taxon_gbif=taxon
            ).models(BiologicalCollectionRecord)

        results = results.filter(
            validated=True
        )
        # get by bbox
        if not ignore_bbox:
            bbox = request_data.get('bbox', None)
            if bbox:
                bbox_array = bbox.split(',')
                downtown_bottom_left = Point(
                    float(bbox_array[1]),
                    float(bbox_array[0]))

                downtown_top_right = Point(
                    float(bbox_array[3]),
                    float(bbox_array[2]))

                results = results.within(
                    'location_center',
                    downtown_bottom_left,
                    downtown_top_right)

        # additional filters
        # query by collectors
        query_collector = request_data.get('collector')
        if query_collector:
            qs_collector = SQ()
            qs = json.loads(query_collector)
            for query in qs:
                qs_collector.add(SQ(collector=query), SQ.OR)
            results = results.filter(qs_collector)

        boundary = request_data.get('boundary')
        if boundary:
            qs_collector = SQ()
            qs = json.loads(boundary)
            for query in qs:
                qs_collector.add(SQ(boundary=query), SQ.OR)
            results = results.filter(qs_collector)

        # query by category
        query_category = request_data.get('category')
        if query_category:
            qs_category = SQ()
            qs = json.loads(query_category)
            for query in qs:
                qs_category.add(SQ(category=query), SQ.OR)
            results = results.filter(qs_category)

        # query by year from
        year_from = request_data.get('yearFrom')
        if year_from:
            clean_query_year_from = sqs.query.clean(year_from)
            results = results.filter(
                collection_date_year__gte=clean_query_year_from)

        # query by year to
        year_to = request_data.get('yearTo')
        if year_to:
            clean_query_year_to = sqs.query.clean(year_to)
            results = results.filter(
                collection_date_year__lte=clean_query_year_to)

        # query by months
        months = request_data.get('months')
        if months:
            qs = months.split(',')
            qs_month = SQ()
            for month in qs:
                clean_query_month = sqs.query.clean(month)
                qs_month.add(
                    SQ(collection_date_month=clean_query_month), SQ.OR)
            results = results.filter(qs_month)
        return results


class GetCollectionExtent(GetCollectionAbstract):
    """
    Return extent of collection
    """

    def get(self, request, format=None):
        results = self.apply_filter(request, ignore_bbox=True)
        multipoint = MultiPoint([result.location_center for result in results])
        if multipoint:
            extents = multipoint.extent
            extents = [
                extents[1], extents[0], extents[3], extents[2]
            ]
            return Response(extents)
        else:
            return Response([])


class CollectionDownloader(GetCollectionAbstract):
    """
    Download all collections with format
    """

    def convert_to_cvs(self, queryset, ModelSerializer):
        """
        Converting data to csv.
        :param queryset: queryset that need to be converted
        :type queryset: QuerySet
        """
        from bims.tasks.collection_record import download_data_to_csv

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="download.csv"'

        if not queryset:
            return JsonResponse({
                'status': 'failed',
                'message': 'Data is empty'
            })

        # Filename
        today_date = datetime.date.today()
        filename = md5(
            '%s%s%s' % (
                json.dumps(self.request.GET),
                queryset.count(),
                today_date)
        ).hexdigest()
        filename += '.csv'

        # Check if filename exists
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

    def convert_to_pdf(self, queryset):
        return JsonResponse({
            'status': 'processing',
            'filename': 'pdf file',
        })

    def get(self, request):
        file_type = request.GET.get('fileType', None)
        if not file_type:
            file_type = 'csv'
        queryset = self.apply_filter(request, ignore_bbox=True)
        if file_type == 'csv':
            return self.convert_to_cvs(
                queryset,
                BioCollectionOneRowSerializer)
        elif file_type == 'geojson':
            return self.convert_to_geojson(
                queryset,
                BiologicalCollectionRecord,
                BioCollectionGeojsonSerializer)
        elif file_type == 'pdf':
            return self.convert_to_pdf(queryset)
        else:
            return Response([])


class ClusterCollection(GetCollectionAbstract):
    """
    Clustering collection with same taxon
    """

    def clustering_process(
            self, records, zoom, pix_x, pix_y):
        """
        Iterate records and create point clusters
        We use a simple method that for every point, that is not within any
        cluster, calculate it's 'catchment' area and add it to the cluster
        If a point is within a cluster 'catchment' area increase point
        count for that cluster and recalculate clusters minimum bbox

        :param records: list of records.
        :type records: list

        :param zoom: zoom level of map
        :type zoom: int

        :param pix_x: pixel x of icon
        :type pix_x: int

        :param pix_y: pixel y of icon
        :type pix_y: int
        """

        cluster_points = []
        for record in records:
            # get x,y of site
            record = record.object
            x = record.site.geometry_point.x
            y = record.site.geometry_point.y

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
                serializer = BioCollectionSerializer(
                    record)
                new_cluster = {
                    'count': 1,
                    'bbox': bbox,
                    'coordinates': [x, y],
                    'record': serializer.data
                }

                cluster_points.append(new_cluster)

        return cluster_points

    def get(self, request, format=None):
        zoom = request.GET.get('zoom', None)
        icon_pixel_x = request.GET.get('icon_pixel_x', None)
        icon_pixel_y = request.GET.get('icon_pixel_y', None)

        if not zoom or not icon_pixel_x or not icon_pixel_y:
            return HttpResponseBadRequest(
                'zoom, icon_pixel_x, and icon_pixel_y need to be '
                'in parameters. '
                'zoom : zoom level of map. '
                'icon_pixel_x: size x of icon in pixel. '
                'icon_pixel_y: size y of icon in pixel. ')
        results = self.apply_filter(request)
        cluster = self.clustering_process(
            results, int(float(zoom)), int(icon_pixel_x), int(icon_pixel_y)
        )
        return Response(geo_serializer(cluster)['features'])
