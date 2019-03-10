# coding=utf8
import json
import os
from django.contrib.gis.geos import Polygon
from django.db.models import Q, F, Count
from django.db.models.functions import ExtractYear
from django.http import Http404, HttpResponseBadRequest
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.serializers.location_site_serializer import (
    LocationSiteSerializer,
    LocationSiteClusterSerializer,
    LocationSitesCoordinateSerializer
)
from bims.serializers.location_site_detail_serializer import \
    LocationSiteDetailSerializer
from bims.utils.cluster_point import (
    within_bbox,
    overlapping_area,
    update_min_bbox,
    geo_serializer
)
from bims.api_views.collection import GetCollectionAbstract
from bims.utils.search_process import (
    get_or_create_search_process,
    create_search_process_file
)
from bims.models.search_process import SITES_SUMMARY
from bims.api_views.search_version_2 import SearchVersion2


class LocationSiteList(APIView):
    """
    List all location site
    """

    def get(self, request, *args):
        location_site = LocationSite.objects.all()
        # get by bbox
        bbox = request.GET.get('bbox', None)
        if bbox:
            geom_bbox = Polygon.from_bbox(
                tuple([float(edge) for edge in bbox.split(',')]))
            location_site = location_site.filter(
                Q(geometry_point__intersects=geom_bbox) |
                Q(geometry_line__intersects=geom_bbox) |
                Q(geometry_polygon__intersects=geom_bbox) |
                Q(geometry_multipolygon__intersects=geom_bbox)
            )
        serializer = LocationSiteSerializer(location_site, many=True)
        return Response(serializer.data)


class LocationSiteDetail(APIView):
    """
    Return detail of location site
    """

    def get_object(self, pk):
        try:
            return LocationSite.objects.get(pk=pk)
        except LocationSite.DoesNotExist:
            raise Http404

    def get(self, request):
        site_id = request.GET.get('siteId')
        query_value = request.GET.get('search')
        filters = request.GET

        # Search collection
        (
            collection_results,
            site_results,
            fuzzy_search
        ) = GetCollectionAbstract.apply_filter(
            query_value,
            filters,
            ignore_bbox=True)

        collection_ids = []
        if collection_results:
            collection_ids = list(collection_results.values_list(
                'model_pk',
                flat=True))
        context = {
            'collection_ids': collection_ids
        }
        location_site = self.get_object(site_id)
        serializer = LocationSiteDetailSerializer(
            location_site,
            context=context)
        return Response(serializer.data)


class LocationSiteClusterList(APIView):
    """
    List all location site in cluster
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
            centroid = record.get_centroid()
            if not centroid:
                continue
            x = centroid.x
            y = centroid.y

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
                    record)
                new_cluster = {
                    'count': 1,
                    'bbox': bbox,
                    'coordinates': [x, y],
                    'record': serializer.data
                }

                cluster_points.append(new_cluster)

        return cluster_points

    def get(self, request, *args):
        location_site = LocationSite.objects.all()
        # get by bbox
        zoom = request.GET.get('zoom', None)
        bbox = request.GET.get('bbox', None)
        icon_pixel_x = request.GET.get('icon_pixel_x', None)
        icon_pixel_y = request.GET.get('icon_pixel_y', None)

        if not zoom or not icon_pixel_x or not icon_pixel_y:
            return HttpResponseBadRequest(
                'zoom, icon_pixel_x, and icon_pixel_y need to be '
                'in parameters. '
                'zoom : zoom level of map. '
                'icon_pixel_x: size x of icon in pixel. '
                'icon_pixel_y: size y of icon in pixel. ')
        if bbox:
            geom_bbox = Polygon.from_bbox(
                tuple([float(edge) for edge in bbox.split(',')]))

            sites_ids = BiologicalCollectionRecord.objects.filter(
                validated=True).filter(
                Q(site__geometry_point__intersects=geom_bbox) |
                Q(site__geometry_line__intersects=geom_bbox) |
                Q(site__geometry_polygon__intersects=geom_bbox) |
                Q(site__geometry_multipolygon__intersects=geom_bbox)
            ).values('site').distinct()
            location_site = location_site.filter(
                id__in=sites_ids
            )
        cluster = self.clustering_process(
            location_site,
            int(float(zoom)),
            int(icon_pixel_x),
            int(icon_pixel_y)
        )
        return Response(geo_serializer(cluster)['features'])


class LocationSitesSummary(APIView):
    """
        List cached location site summary based on collection record search.
    """
    COUNT = 'count'
    ORIGIN = 'origin'
    TOTAL_RECORDS = 'total_records'
    RECORDS_GRAPH_DATA = 'records_graph_data'
    RECORDS_OCCURRENCE = 'records_occurrence'
    TAXA_OCCURRENCE = 'taxa_occurrence'
    CATEGORY_SUMMARY = 'category_summary'
    TAXONOMY_NAME = 'name'
    TAXA_GRAPH = 'taxa_graph'
    ORIGIN_OCCURRENCE = 'origin_occurrence'
    CONS_STATUS_OCCURRENCE = 'cons_status_occurrence'

    def get(self, request):
        filters = request.GET
        search = SearchVersion2(filters)
        collection_results = search.process_search()

        search_process, created = get_or_create_search_process(
            SITES_SUMMARY,
            query=request.build_absolute_uri()
        )

        if search_process.file_path:
            if os.path.exists(search_process.file_path):
                try:
                    raw_data = open(search_process.file_path)
                    return Response(json.load(raw_data))
                except ValueError:
                    pass

        taxa_occurrence = self.get_site_taxa_occurrences_per_year(
            collection_results)


        taxa_graph_data = collection_results.annotate(
            year=ExtractYear('collection_date'),
            name=F('taxonomy__scientific_name'),
        ).annotate(
            count=Count('year')
        ).values(
            'year', 'name', 'count'
        ).order_by('year')
        taxa_graph = self.get_data_per_year(taxa_graph_data)

        records_occurrence = collection_results.annotate(
            name=F('taxonomy__scientific_name'),
            taxon_id=F('taxonomy_id'),
            origin=F('category')
        ).values(
            'taxon_id', 'name', 'origin'
        ).annotate(
            count=Count('taxonomy')
        )

        records_graph_data = collection_results.annotate(
            year=ExtractYear('collection_date'),
            origin=F('category')
        ).values(
            'year', 'origin'
        ).annotate(
            count=Count('year')
        ).order_by('year')

        category_summary = collection_results.annotate(
            origin=F('category')
        ).values_list(
            'origin'
        ).annotate(
            count=Count('category')
        )

        origin_occurrence = self.get_origin_occurrence_data(collection_results)
        search_process.set_search_raw_query(
            search.location_sites_raw_query
        )
        cons_status_occurrence = self.get_cons_status_occurrence_data(
            collection_results)

        search_process.create_view()

        response_data = {
            self.TOTAL_RECORDS: len(collection_results),
            self.RECORDS_GRAPH_DATA: list(records_graph_data),
            self.TAXA_OCCURRENCE: dict(taxa_occurrence),
            self.RECORDS_OCCURRENCE: list(records_occurrence),
            self.CATEGORY_SUMMARY: dict(category_summary),
            self.TAXA_GRAPH: dict(taxa_graph),
            self.ORIGIN_OCCURRENCE: dict(origin_occurrence),
            self.CONS_STATUS_OCCURRENCE: dict(cons_status_occurrence),
            'process': search_process.process_id,
            'extent': search.extent(),
            'sites_raw_query': search_process.process_id
        }

        file_path = create_search_process_file(
            data=response_data,
            search_process=search_process,
            finished=True
        )
        file_data = open(file_path)

        try:
            return Response(json.load(file_data))
        except ValueError:
            return Response(response_data)

    def get_site_taxa_occurrences_per_year(self, collection_results):
        taxa_occurrence_data = collection_results.annotate(
            year=ExtractYear('collection_date'),
        ).values('year'
                 ).annotate(count=Count('year')
                            ).values('year', 'count'
                                     ).order_by('year')
        result = {}
        result['occurrences_line_chart'] = {}
        result['occurrences_line_chart']['values'] = []
        result['occurrences_line_chart']['keys'] = []
        result['occurrences_line_chart']['title'] \
            = 'Occurrences'
        for each_record in taxa_occurrence_data:
            result['occurrences_line_chart']['keys'].append(
                each_record['year'])
            result['occurrences_line_chart']['values'].append(
                each_record['count'])
        return result

    def get_data_per_year(self, data_in):
        unique_name_list = []
        unique_year_list = []
        unparsed_data = {}

        for each_record in data_in:
            unparsed_count = 0
            unparsed_year = 0
            unparsed_name = 'Unknown'
            if 'count' in each_record:
                unparsed_count = each_record['count']
            if 'year' in each_record:
                unparsed_year = each_record['year']
            if 'name' in each_record:
                unparsed_name = each_record['name']
            if unparsed_year not in unique_year_list:
                unique_year_list.append(unparsed_year)
            if unparsed_name not in unparsed_data:
                unparsed_data[unparsed_name] = {}
            if unparsed_year not in unparsed_data[unparsed_name]:
                unparsed_data[unparsed_name][unparsed_year] = unparsed_count
            if unparsed_name not in unique_name_list:
                unique_name_list.append(unparsed_name)

        parsed_data = {}
        unique_name_list.sort()
        unique_year_list.sort()
        for each_name in unique_name_list:
            if each_name not in parsed_data:
                parsed_data[each_name] = []
            for each_year in unique_year_list:
                if each_year in unparsed_data[each_name]:
                    parsed_data[each_name].append(str(
                        unparsed_data[each_name][each_year]
                    ))
                else:
                    parsed_data[each_name].append(str(0))

        result = {}
        result['data'] = parsed_data
        result['labels'] = unique_year_list
        result['dataset_labels'] = unique_name_list
        return result

    def get_origin_occurrence_data(self, collection_records):
        origin_graph_data = collection_records.annotate(
            year=ExtractYear('collection_date'),
            name=F('category'),
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('year')
        result = self.get_data_per_year(origin_graph_data)
        return result

    def get_cons_status_occurrence_data(self, collection_records):
        origin_graph_data = collection_records.annotate(
            year=ExtractYear('collection_date'),
            name=F('taxonomy__iucn_status__category'),
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('year')
        result = self.get_data_per_year(origin_graph_data)
        return result


class LocationSitesCoordinate(ListAPIView):
    """
        List paginated location site based on collection record search,
        there may be duplication.
    """
    serializer_class = LocationSitesCoordinateSerializer

    def get_queryset(self):
        query_value = self.request.GET.get('search')
        filters = self.request.GET
        (
            collection_results,
            site_results,
            fuzzy_search
        ) = GetCollectionAbstract.apply_filter(
            query_value,
            filters,
            ignore_bbox=True,
            only_site=True)
        return collection_results
