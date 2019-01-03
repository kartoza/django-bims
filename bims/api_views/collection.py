# coding=utf8

import json
from hashlib import md5
import datetime
import os
import errno
from haystack.query import SearchQuerySet, SQ, EmptySearchQuerySet
from django.contrib.gis.geos import MultiPoint, Point
from django.http import HttpResponse, JsonResponse
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
    update_min_bbox
)
from bims.models.user_boundary import UserBoundary
from bims.models.search_process import SearchProcess
from bims.utils.url import remove_params_from_uri


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
        settings.ELASTIC_MIN_SCORE = 0
        sqs = SearchQuerySet()
        results = sqs.all().models(
            BiologicalCollectionRecord)
        results = results.filter(validated=True)
        return results

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

        fuzzy_search = False
        user_boundaries = None
        filter_mode = False

        sqs = SearchQuerySet()
        settings.ELASTIC_MIN_SCORE = 0

        # All filters
        taxon = filters.get('taxon', None)
        bbox = filters.get('bbox', None)
        query_collector = filters.get('collector', None)
        boundary = filters.get('boundary', None)
        user_boundary = filters.get('userBoundary', None)
        query_category = filters.get('category', None)
        reference_category = filters.get('referenceCategory', None)
        reference = filters.get('reference', None)
        year_from = filters.get('yearFrom', None)
        year_to = filters.get('yearTo', None)
        months = filters.get('months', None)
        site_id = filters.get('siteId', None)
        endemic = filters.get('endemic', None)
        conservation_status = filters.get('conservationStatus', None)
        river_catchments = filters.get('riverCatchment', None)

        if (
                taxon or
                query_collector or
                boundary or user_boundary or
                query_category or reference_category or
                year_from or year_to or
                months or reference or
                conservation_status or
                river_catchments or
                site_id or endemic):
            filter_mode = True

        if query_value:
            clean_query = sqs.query.clean(query_value)
            results = sqs.filter(
                SQ(original_species_name_exact__contains=clean_query) |
                SQ(taxon_scientific_name_exact__contains=clean_query) |
                SQ(vernacular_names__contains=clean_query),
                validated=True
            ).models(BiologicalCollectionRecord)

            if len(results) > 0:
                fuzzy_search = False
            else:
                fuzzy_search = True
                # Set min score bigger for fuzzy search
                settings.ELASTIC_MIN_SCORE = 2
                results = sqs.filter(
                    SQ(original_species_name=clean_query),
                    validated=True
                ).models(BiologicalCollectionRecord)
                settings.ELASTIC_MIN_SCORE = 0
        else:
            if filter_mode:
                results = sqs.all().models(
                    BiologicalCollectionRecord)
                results = results.filter(validated=True)
            else:
                results = []

        if taxon:
            results = sqs.filter(
                taxonomy=taxon
            ).models(BiologicalCollectionRecord)

        # get by bbox
        if not ignore_bbox:
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
        if query_collector:
            qs_collector = SQ()
            qs = json.loads(query_collector)
            for query in qs:
                qs_collector.add(SQ(collector=query), SQ.OR)
            results = results.filter(qs_collector)

        if boundary:
            qs_collector = SQ()
            qs = json.loads(boundary)
            for query in qs:
                query = '_' + query + '_'
                qs_collector.add(SQ(boundary__contains=query), SQ.OR)
            results = results.filter(qs_collector)

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
        if query_category:
            qs_category = SQ()
            qs = json.loads(query_category)
            for query in qs:
                qs_category.add(SQ(category=query), SQ.OR)
            results = results.filter(qs_category)

        # query by endemic
        if endemic:
            qs_endemism = SQ()
            qs = json.loads(endemic)
            for query in qs:
                qs_endemism.add(SQ(endemism=query), SQ.OR)
            results = results.filter(qs_endemism)

        # query by conservation status
        if conservation_status:
            qs_conservation_status = SQ()
            qs = json.loads(conservation_status)
            for query in qs:
                qs_conservation_status.add(SQ(iucn_status=query), SQ.OR)
            results = results.filter(qs_conservation_status)

        # query by river catchment
        if river_catchments:
            qs_river_catchment = SQ()
            qs = json.loads(river_catchments)
            for query in qs:
                query = '_' + query + '_'
                qs_river_catchment.add(SQ(river_catchments__contains=query),
                                       SQ.OR)
            results = results.filter(qs_river_catchment)

        # query by reference category
        if reference_category:
            qs_reference_category = SQ()
            qs = json.loads(reference_category)
            for query in qs:
                qs_reference_category.add(SQ(reference_category=query), SQ.OR)
            results = results.filter(qs_reference_category)

        # query by reference category
        if reference:
            qs_reference = SQ()
            qs = json.loads(reference)
            for query in qs:
                qs_reference.add(SQ(reference__exact=query),
                                 SQ.OR)
            results = results.filter(qs_reference)

        # query by year from
        if year_from:
            clean_query_year_from = sqs.query.clean(year_from)
            results = results.filter(
                collection_date_year__gte=clean_query_year_from)

        # query by year to
        if year_to:
            clean_query_year_to = sqs.query.clean(year_to)
            results = results.filter(
                collection_date_year__lte=clean_query_year_to)

        # query by months
        if months:
            qs = months.split(',')
            qs_month = SQ()
            for month in qs:
                clean_query_month = sqs.query.clean(month)
                qs_month.add(
                    SQ(collection_date_month=clean_query_month), SQ.OR)
            results = results.filter(qs_month)

        # Search by site id
        if site_id:
            site_ids = site_id.split(',')
            qs_site_id = SQ()
            for site in site_ids:
                qs_site_id.add(
                    SQ(site_id_indexed=site), SQ.OR
                )
            results = results.filter(
                qs_site_id
            ).models(BiologicalCollectionRecord)

        collection_results = results

        # Search location site by name
        location_site_search = EmptySearchQuerySet()
        if query_value:
            location_site_search = SearchQuerySet().filter(
                site_name__contains=query_value
            ).models(LocationSite)

        location_site_results = location_site_search
        location_site_user_boundary = EmptySearchQuerySet()

        if boundary:
            qs_collector = SQ()
            qs = json.loads(boundary)
            for query in qs:
                query = '_' + query + '_'
                qs_collector.add(SQ(boundary__contains=query), SQ.OR)
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
                            geom)

        site_results = GetCollectionAbstract.combine_search_query_results(
            location_site_results,
            location_site_user_boundary
        )

        if len(site_results) > 0 or isinstance(
                location_site_user_boundary, SearchQuerySet):
            # If there are fuzzy results from collection search but we
            # got non fuzzy results from location site, then remove
            # all the fuzzy results from collection
            if fuzzy_search and \
                    len(collection_results) > 0:
                collection_results = []
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
        filename = md5(
            '%s%s%s' % (
                search_uri,
                query_count,
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
        is_using_filters = self.is_using_filters(request.GET)
        if not file_type:
            file_type = 'csv'
        site_results = None

        if is_using_filters or query_value:
            collection_results, \
                site_results, \
                fuzzy_search = self.apply_filter(
                    query_value,
                    filters,
                    ignore_bbox=True)
        else:
            collection_results = self.get_all_validated()

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
