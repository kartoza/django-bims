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
from bims.models.location_site import LocationSite
from bims.serializers.bio_collection_serializer import (
    BioCollectionOneRowSerializer,
    BioCollectionGeojsonSerializer
)
from bims.serializers.location_site_serializer import \
    LocationSiteClusterSerializer
from bims.utils.cluster_point import (
    within_bbox,
    overlapping_area,
    update_min_bbox,
    geo_serializer
)
from bims.models.user_boundary import UserBoundary


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
    def apply_filter(query_value, filters, ignore_bbox=False):
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

        fuzzy_search = False
        user_boundaries = None

        sqs = SearchQuerySet()
        settings.ELASTIC_MIN_SCORE = 0

        if query_value:
            clean_query = sqs.query.clean(query_value)
            results = SearchQuerySet().filter(
                    SQ(original_species_name_exact__contains=clean_query) |
                    SQ(taxon_common_name_exact__contains=clean_query) |
                    SQ(taxon_scientific_name_exact__contains=clean_query),
                    validated=True
            ).models(BiologicalCollectionRecord)

            if len(results) > 0:
                fuzzy_search = False
            else:
                fuzzy_search = True
                # Set min score bigger for fuzzy search
                settings.ELASTIC_MIN_SCORE = 2
                results = SearchQuerySet().filter(
                        SQ(original_species_name=clean_query) |
                        SQ(taxon_common_name=clean_query) |
                        SQ(taxon_scientific_name=clean_query),
                        validated=True
                ).models(BiologicalCollectionRecord)
                settings.ELASTIC_MIN_SCORE = 0
        else:
            results = SearchQuerySet().all().models(BiologicalCollectionRecord)
            results = results.filter(validated=True)

        taxon = filters.get('taxon', None)
        if taxon:
            results = sqs.filter(
                taxon_gbif=taxon
            ).models(BiologicalCollectionRecord)

        # get by bbox
        if not ignore_bbox:
            bbox = filters.get('bbox', None)
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
        query_collector = filters.get('collector')
        if query_collector:
            qs_collector = SQ()
            qs = json.loads(query_collector)
            for query in qs:
                qs_collector.add(SQ(collector=query), SQ.OR)
            results = results.filter(qs_collector)

        boundary = filters.get('boundary')
        if boundary:
            qs_collector = SQ()
            qs = json.loads(boundary)
            for query in qs:
                qs_collector.add(SQ(boundary=query), SQ.OR)
            results = results.filter(qs_collector)

        user_boundary = filters.get('userBoundary')
        if user_boundary:
            qs = json.loads(user_boundary)
            user_boundaries = UserBoundary.objects.filter(
                    pk__in=qs
            )
            for user_boundary in user_boundaries:
                for geom in user_boundary.geometry:
                    results = results.polygon(
                            'location_center',
                            geom
                    )

        # query by category
        query_category = filters.get('category')
        if query_category:
            qs_category = SQ()
            qs = json.loads(query_category)
            for query in qs:
                qs_category.add(SQ(category=query), SQ.OR)
            results = results.filter(qs_category)

        # query by year from
        year_from = filters.get('yearFrom')
        if year_from:
            clean_query_year_from = sqs.query.clean(year_from)
            results = results.filter(
                collection_date_year__gte=clean_query_year_from)

        # query by year to
        year_to = filters.get('yearTo')
        if year_to:
            clean_query_year_to = sqs.query.clean(year_to)
            results = results.filter(
                collection_date_year__lte=clean_query_year_to)

        # query by months
        months = filters.get('months')
        if months:
            qs = months.split(',')
            qs_month = SQ()
            for month in qs:
                clean_query_month = sqs.query.clean(month)
                qs_month.add(
                    SQ(collection_date_month=clean_query_month), SQ.OR)
            results = results.filter(qs_month)

        collection_results = results

        # Search location site by name
        location_site_search = []
        if query_value:
            location_site_search = SearchQuerySet().filter(
                    site_name__contains=query_value
            ).models(LocationSite)

        location_site_results = location_site_search
        location_site_user_boundary = None

        if boundary:
            qs_collector = SQ()
            qs = json.loads(boundary)
            for query in qs:
                qs_collector.add(SQ(boundary=query), SQ.OR)
            if isinstance(location_site_results, SearchQuerySet):
                location_site_results = location_site_results.filter(
                        qs_collector)

        if user_boundaries and isinstance(location_site_search,
                                          SearchQuerySet):
            location_site_user_boundary = location_site_search
            for user_boundary in user_boundaries:
                for geom in user_boundary.geometry:
                    location_site_user_boundary = \
                        location_site_user_boundary.polygon(
                            'location_site_point',
                            geom
                    )

        if location_site_user_boundary:
            if boundary:
                site_results = \
                    location_site_results | location_site_user_boundary
            else:
                site_results = location_site_user_boundary
        else:
            site_results = location_site_results

        if len(site_results) > 0:
            # If there are fuzzy results from collection search but we
            # got non fuzzy results from location site, then remove
            # all the fuzzy results from collection
            if fuzzy_search and \
                    len(collection_results) > 0:
                collection_results = []
            fuzzy_search = False

        return collection_results, site_results, fuzzy_search


class GetCollectionExtent(GetCollectionAbstract):
    """
    Return extent of collection
    """

    def get(self, request, format=None):
        query_value = request.GET.get('search')
        filters = request.GET

        collection_results, \
            site_results, \
            fuzzy_search = self.apply_filter(
                query_value,
                filters,
                ignore_bbox=True)

        multipoint = MultiPoint(
                [result.location_center for result in collection_results] +
                [result.location_site_point for result in site_results]
        )
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

    def get(self, request):
        query_value = request.GET.get('search')
        filters = request.GET
        file_type = request.GET.get('fileType', None)
        if not file_type:
            file_type = 'csv'
        collection_results, \
            site_results, \
            fuzzy_search = self.apply_filter(
                query_value,
                filters,
                ignore_bbox=True)
        if file_type == 'csv':
            return self.convert_to_cvs(
                collection_results,
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

    def clustering_process(
            self, records, zoom, pix_x, pix_y):
        """
        Iterate records and create point clusters
        We use a simple method that for every point, that is not within any
        cluster, calculate it's 'catchment' area and add it to the cluster
        If a point is within a cluster 'catchment' area increase point
        count for that cluster and recalculate clusters minimum bbox

        :param records: generator of records.
        :type records: generator

        :param zoom: zoom level of map
        :type zoom: int

        :param pix_x: pixel x of icon
        :type pix_x: int

        :param pix_y: pixel y of icon
        :type pix_y: int
        """

        cluster_points = []
        sites = []
        for record in records:
            # get x,y of site
            if isinstance(record, BiologicalCollectionRecord):
                x = record.site.geometry_point.x
                y = record.site.geometry_point.y
                location_site = record.site
                if record.site.id in sites:
                    continue
                sites.append(record.site_id)
            elif isinstance(record, LocationSite):
                x = record.geometry_point.x
                y = record.geometry_point.y
                location_site = record
                if record.id in sites:
                    continue
                sites.append(record.id)
            else:
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

        return cluster_points

    def get(self, request, format=None):
        zoom = request.GET.get('zoom', None)
        icon_pixel_x = request.GET.get('icon_pixel_x', None)
        icon_pixel_y = request.GET.get('icon_pixel_y', None)
        query_value = request.GET.get('search')
        filters = request.GET

        if not zoom or not icon_pixel_x or not icon_pixel_y:
            return HttpResponseBadRequest(
                'zoom, icon_pixel_x, and icon_pixel_y need to be '
                'in parameters. '
                'zoom : zoom level of map. '
                'icon_pixel_x: size x of icon in pixel. '
                'icon_pixel_y: size y of icon in pixel. ')
        collection_results, \
            site_results, \
            fuzzy_search = self.apply_filter(
                query_value,
                filters)

        results = list(self.queryset_gen(collection_results))
        results += list(self.queryset_gen(site_results))

        cluster = self.clustering_process(
            results, int(float(zoom)), int(icon_pixel_x), int(icon_pixel_y)
        )
        return Response(geo_serializer(cluster)['features'])
