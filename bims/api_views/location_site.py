# coding=utf8
import json
import os
from collections import Counter
from django.contrib.gis.geos import Polygon
from django.db.models import Q, F, Count
from django.db.models.functions import ExtractYear, Concat
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

        taxa_occurrence = collection_results.annotate(
            name=F('taxonomy__scientific_name'),
            year=ExtractYear('collection_date'),
            taxon_id=F('taxonomy_id'),
            # year_taxon_id=Concat('year', 'taxon_id')
        ).values(
            'taxon_id', 'name', 'year'
        ).annotate(
            taxon_count=Count('year')
        )

        # taxa_occurrence = collection_results.annotate(
        #     year=ExtractYear('collection_date'),
        #     name=F('taxonomy__scientific_name')
        # ).values(
        #     'name', 'year'
        # ).annotate(Count('taxonomy'))

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

        taxa_graph = self.get_taxa_per_year(
            collection_results)

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

        search_process.set_search_raw_query(
            search.location_sites_raw_query
        )
        search_process.create_view()

        response_data = {
            self.TOTAL_RECORDS: len(collection_results),
            self.RECORDS_GRAPH_DATA: list(records_graph_data),
            self.TAXA_OCCURRENCE: dict(taxa_occurrence),
            self.RECORDS_OCCURRENCE: list(records_occurrence),
            self.CATEGORY_SUMMARY: dict(category_summary),
            self.TAXA_GRAPH: dict(taxa_graph),
            'process': search_process.process_id,
            'extent': search.extent(),
            'sites_raw_query': search_process.process_id
        }

        # file_path = create_search_process_file(
        #     data=response_data,
        #     search_process=search_process,
        #     finished=True
        # )
        # file_data = open(file_path)

        # try:
        #     return Response(json.load(file_data))
        # except ValueError:
        return Response(response_data)

    def get_site_taxa_occurrences_per_year(self, collection_records):
        result = {}
        occurrences_data = []
        result['occurrences_line_chart'] = {}
        result['occurrences_line_chart']['values'] = []
        result['occurrences_line_chart']['keys'] = []
        result['occurrences_line_chart']['title'] \
            = 'Occurrences'

        for each_record in collection_records:
            occurrences_data.append(each_record.collection_date.year)

        data_counter_occurrences = (
            Counter(occurrences_data))

        result['occurrences_line_chart']['values'].append(
            data_counter_occurrences.values())
        result['occurrences_line_chart']['keys'].append(
            data_counter_occurrences.keys())
        result['occurrences_line_chart']['values'] = (
            result['occurrences_line_chart']['values'][0])
        result['occurrences_line_chart']['keys'] = (
            result['occurrences_line_chart']['keys'][0])

        return result


    def get_data_per_year(self, data_in):
        yearly_data  = {}
        unique_year_list = []
        unique_name_list = []
        for each_record in data_in:
            record_count = 0
            record_year = 0
            record_name = 'Unknown'
            if 'count' in each_record:
                record_count = each_record['count']
            if 'year' in each_record:
                record_year = each_record['year']
            if 'name' in each_record:
                record_name = each_record['name']
            if record_year not in unique_year_list and record_year > 0:
                unique_year_list.append(record_year)
            if record_name not in yearly_data:
                yearly_data[record_name] = []
                unique_name_list.append(record_name)
            if record_year not in yearly_data[record_name]:
                yearly_data[record_name].append(record_count)
        result = {}
        result['data'] = yearly_data
        result['labels'] = unique_year_list
        result['dataset_labels'] = unique_name_list
        return result



    def get_taxa_per_year(self, collection_records):
        taxa_data = {}
        unique_year_list = []

        for each_record in collection_records:
            scientific_name = str(each_record.taxonomy.scientific_name)
            collection_year = str(each_record.collection_date.year)
            if collection_year not in unique_year_list:
                unique_year_list.append(collection_year)
            if scientific_name not in taxa_data:
                taxa_data[scientific_name] = {}
            if collection_year not in taxa_data[scientific_name]:
                taxa_data[scientific_name][collection_year] = 0
            taxa_data[scientific_name][collection_year] += 1

        unique_fish_list = list(taxa_data.keys())
        unique_fish_list.sort()

        unique_year_list.sort()
        fish_data = {}
        for fish_key in unique_fish_list:
            if fish_key not in fish_data:
                fish_data[fish_key] = []
            for each_year in unique_year_list:
                if each_year in taxa_data[fish_key]:
                    fish_data[fish_key].append(str(
                        taxa_data[fish_key][each_year]))
                else:
                    fish_data[fish_key].append(str(0))

        result = {}
        result['data'] = fish_data
        result['labels'] = unique_year_list
        result['dataset_labels'] = unique_fish_list

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
