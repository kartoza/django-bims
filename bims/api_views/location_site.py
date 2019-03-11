# coding=utf8
import json
import os
from collections import Counter
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
from bims.models.iucn_status import IUCNStatus
from bims.api_views.search_version_2 import SearchVersion2
from bims.enums.taxonomic_rank import TaxonomicRank


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
    CATEGORY_SUMMARY = 'category_summary'
    TAXONOMY_NAME = 'name'
    BIODIVERSITY_DATA = 'biodiversity_data'

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

        biodiversity_data = self.get_biodiversity_data(collection_results)

        response_data = {
            self.TOTAL_RECORDS: len(collection_results),
            self.RECORDS_GRAPH_DATA: list(records_graph_data),
            self.RECORDS_OCCURRENCE: list(records_occurrence),
            self.CATEGORY_SUMMARY: dict(category_summary),
            self.BIODIVERSITY_DATA: dict(biodiversity_data),
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
        #
        # try:
        #     return Response(json.load(file_data))
        # except ValueError:
        return Response(response_data)


    def get_biodiversity_data(self, collection_results):
        biodiversity_data = {}
        biodiversity_data['fish'] = {}
        biodiversity_data['fish']['origin_chart'] = {}
        biodiversity_data['fish']['cons_status_chart'] = {}
        biodiversity_data['fish']['endemism_chart'] = {}

        origin_by_name_data = collection_results.annotate(
            name=F('category')
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )
        keys = []
        values = []
        for each_record in origin_by_name_data:
            try:
                new_name = BiologicalCollectionRecord.retrieve_category_choice(
                    each_record['name'])
                keys.append(new_name)
            except KeyError:
                keys.append('Unknown')
            try:
                values.append(each_record['count'])
            except KeyError:
                keys.append('Unknown')

        biodiversity_data['fish']['origin_chart']['data'] = values
        biodiversity_data['fish']['origin_chart']['keys'] = keys

        IUCN_status_object = IUCNStatus.objects.create()
        cons_status_data = collection_results.annotate(
            name=F('taxonomy__iucn_status__category')
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )

        keys = []
        values = []
        for each_record in cons_status_data:
            try:
                next_name = IUCN_status_object.get_title(each_record['name'])
                keys.append(next_name)
            except KeyError:
                keys.append('Unknown')
            try:
                values.append(each_record['count'])
            except KeyError:
                keys.append('Unknown')

        biodiversity_data['fish']['cons_status_chart']['data'] = values
        biodiversity_data['fish']['cons_status_chart']['keys'] = keys
        endemism_status_data = collection_results.annotate(
            name=F('taxonomy__endemism__name')
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )

        keys = []
        values = []
        for each_record in endemism_status_data:
            try:
                new_name = keys.append(each_record['name'])
                keys.append(new_name)
            except KeyError:
                keys.append('Unknown')
            try:
                values.append(each_record['count'])
            except KeyError:
                keys.append('Unknown')

        biodiversity_data['fish']['endemism_chart']['data'] = values
        biodiversity_data['fish']['endemism_chart']['keys'] = keys

        taxa = self.get_origin_cons_endemsim_data(collection_results)

        biodiversity_data['taxa'] = taxa
        biodiversity_data['occurrences'] = [0, 0, 0]
        biodiversity_data['occurrences'][0] = (
            sum(taxa['Actinopterygii']['occurrences']))
        biodiversity_data['number_of_taxa'] = [0, 0, 0]
        biodiversity_data['number_of_taxa'][0] = (
            len(taxa['Actinopterygii']['number_of_taxa']))
        biodiversity_data['ecological_condition'] = ['TBA', 'TBA', 'TBA']
        return biodiversity_data


    def get_origin_cons_endemsim_data(self, collections):
        taxa = {}
        for model in collections:
            taxonomy_class_name = model.taxonomy.class_name
            if not (taxonomy_class_name in taxa):
                taxa[taxonomy_class_name] = {}
                taxa[taxonomy_class_name]['origin_data'] = []
                taxa[taxonomy_class_name]['cons_status_data'] = []
                taxa[taxonomy_class_name]['endemism_data'] = []
                taxa[taxonomy_class_name]['occurrence_data'] = []
            taxa[taxonomy_class_name]['origin_data'].append(
                model.category)
            try:
                iucn_category = model.taxonomy.iucn_status.category
                iucn_name = model.taxonomy.iucn_status.get_status()
                iucn_title = ('({iucn_category}) {iucn_name}'.format(
                    iucn_category=iucn_category,
                    iucn_name=iucn_name))
            except AttributeError:
                iucn_title = 'Unknown'
            taxa[taxonomy_class_name]['cons_status_data'].append(
                iucn_title)
            if str(model.taxonomy.endemism) == 'None':
                endemism_title = 'Unknown'
            else:
                endemism_title = str(model.taxonomy.endemism)

            taxa[taxonomy_class_name]['endemism_data'].append(
                endemism_title)
            try:
                scientific_name = str(model.taxonomy.endemism)
            except KeyError:
                scientific_name = 'Unknown'

            taxa[taxonomy_class_name]['occurrence_data'].append(
                scientific_name)

        for class_name in taxa:
            if 'origin_chart' not in taxa[class_name]:
                taxa[class_name]['origin_chart'] = {}
                taxa[class_name]['origin_chart']['data'] = []
                taxa[class_name]['origin_chart']['keys'] = []
                taxa[class_name]['cons_status_chart'] = {}
                taxa[class_name]['cons_status_chart']['data'] = []
                taxa[class_name]['cons_status_chart']['keys'] = []
                taxa[class_name]['endemism_chart'] = {}
                taxa[class_name]['endemism_chart']['data'] = []
                taxa[class_name]['endemism_chart']['keys'] = []
                taxa[class_name]['occurrences'] = []
                taxa[class_name]['number_of_taxa'] = []

            data_counter_origin = (
                Counter(taxa[class_name]['origin_data']))
            data_counter_cons_status = (
                Counter(taxa[class_name]['cons_status_data']))
            data_counter_endemism = (
                Counter(taxa[class_name]['endemism_data']))
            data_counter_occurrence = (
                Counter(taxa[class_name]['occurrence_data']))

            taxa[class_name]['origin_chart']['data'].append(
                data_counter_origin.values())
            taxa[class_name]['origin_chart']['keys'].append(
                data_counter_origin.keys())

            taxa[class_name]['origin_chart']['data'] = (
                taxa[class_name]['origin_chart']['data'][0])
            taxa[class_name]['origin_chart']['keys'] = (
                taxa[class_name]['origin_chart']['keys'][0])
            for index, each in enumerate(
                    taxa[class_name]['origin_chart']['keys']):
                taxa[class_name]['origin_chart']['keys'][index] = (
                    str(each).capitalize())

            taxa[class_name]['cons_status_chart']['data'].append(
                data_counter_cons_status.values())


            taxa[class_name]['cons_status_chart']['data'] = (
                taxa[class_name]['cons_status_chart']['data'][0])
            taxa[class_name]['cons_status_chart']['keys'].append(
                data_counter_cons_status.keys())
            taxa[class_name]['cons_status_chart']['keys'] = (
                taxa[class_name]['cons_status_chart']['keys'][0])

            taxa[class_name]['endemism_chart']['data'].append(
                data_counter_endemism.values()[0])
            taxa[class_name]['endemism_chart']['keys'].append(
                data_counter_endemism.keys()[0])
            taxa[class_name]['occurrences'].append(
                data_counter_occurrence.values()[0])
            taxa[class_name]['number_of_taxa'].append(
                data_counter_occurrence.keys()[0])
        return taxa


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
