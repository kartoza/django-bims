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
from sass.models.river import River


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
    SITE_DETAILS = 'site_details'

    def get(self, request):
        filters = request.GET
        search = SearchVersion2(filters)
        collection_results = search.process_search()

        site_id = filters['siteId']
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
        site_details = self.get_site_details(site_id)
        site_details['records_and_sites'] = self.get_number_of_records_and_taxa(
            collection_results)
        site_details['origins_data'] = self.get_origin_data(
            collection_results)
        search_process.set_search_raw_query(
            search.location_sites_raw_query
        )
        search_process.create_view()

        response_data = {
            self.TOTAL_RECORDS: len(collection_results),
            self.RECORDS_GRAPH_DATA: list(records_graph_data),
            self.RECORDS_OCCURRENCE: list(records_occurrence),
            self.CATEGORY_SUMMARY: dict(category_summary),
            self.SITE_DETAILS: dict(site_details),

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

    def get_site_details(self, site_id):
        # get single site detailed dashboard overview data
        location_sites = LocationSite.objects.filter(id=site_id).all()
        site_longitude = self.parse_string(
            str(location_sites.values('longitude')[0]['longitude']))
        site_latitude = self.parse_string(
            str(location_sites.values('latitude')[0]['latitude']))
        site_description = self.parse_string(str(location_sites.values(
                'site_description')[0]['site_description']))
        try:
            context_document = dict(json.loads(str(
            location_sites.values('location_context')[0]['location_context'])))
        except ValueError:
            context_document = ''
        site_river_id = location_sites.values('river_id')[0]['river_id']
        try:
            site_river = River.objects.filter(
                id=site_river_id).values('name')[0]['name']
        except IndexError:
            site_river = 'Unknown'
        overview = {}
        overview['title'] = []
        overview['value'] = []
        catchments = {}
        catchments['title'] = []
        catchments['value'] = []
        sa_ecoregions = {}
        sa_ecoregions['title'] = []
        sa_ecoregions['value'] = []
        sub_water_management_areas = {}
        sub_water_management_areas['title'] = []
        sub_water_management_areas['value'] = []

        overview['title'].append('FBIS Site Code')
        overview['value'].append(str(site_id))

        overview['title'].append('Site coordinates')
        overview['value'].append(
            str('Longitude: {site_longitude}, '
                'Latitude: {site_latitude}').format(
                site_longitude = site_longitude,
                site_latitude = site_latitude))

        overview['title'].append('Site description')
        overview['value'].append(site_description)

        overview['title'].append('River')
        overview['value'].append(site_river)
        if 'context_group_values' in context_document:
            if 'eco_geo_group' in context_document:
                eco_region = (context_document
                              ['context_group_values']
                              ['eco_geo_group']
                              ['service_registry_values']
                              ['eco_region']
                              ['value'])
                geo_class = (context_document
                             ['context_group_values']
                             ['eco_geo_group']
                             ['service_registry_values']
                             ['geo_class']
                             ['value'])
                geo_zone = ('{geo_class} {eco_region}'.format(
                    geo_class=geo_class,
                    eco_region=eco_region))
            else:
                geo_zone = 'Unknown'
        else:
            geo_zone = 'Unknown'

        overview['title'].append('Geomorphological zone')
        overview['value'].append(geo_zone)

        overview['title'].append('River Management Units')
        overview['value'].append('???')

        # Catchments
        if 'context_group_values' in context_document:
            if 'water_group' in context_document:
                primary_catchment = (context_document
                                     ['context_group_values']
                                     ['water_group']
                                     ['service_registry_values']
                                     ['primary_catchment_area']
                                     ['value'])
                secondary_catchment = (context_document
                                       ['context_group_values']
                                       ['water_group']
                                       ['service_registry_values']
                                       ['secondary_catchment_area']
                                       ['value'])
                tertiary_catchment_area = (context_document
                                           ['context_group_values']
                                           ['water_group']
                                           ['service_registry_values']
                                           ['tertiary_catchment_area']
                                           ['value'])
                water_management_areas = (context_document
                                          ['context_group_values']
                                          ['water_group']
                                          ['service_registry_values']
                                          ['water_management_area']
                                          ['value'])
            else:
                primary_catchment = 'Unknown'
                secondary_catchment = 'Unknown'
                tertiary_catchment_area = 'Unknown'
                water_management_areas = 'Unknown'
        else:
            primary_catchment = 'Unknown'
            secondary_catchment = 'Unknown'
            tertiary_catchment_area = 'Unknown'
            water_management_areas = 'Unknown'

        catchments['title'].append('Primary')
        catchments['value'].append(primary_catchment)

        catchments['title'].append('Secondary')
        catchments['value'].append(secondary_catchment)

        catchments['title'].append('Tertiary')
        catchments['value'].append(tertiary_catchment_area)

        catchments['title'].append('Quaternary')
        catchments['value'].append('Coming Soon')

        catchments['title'].append('Quinary')
        catchments['value'].append('very soon...')



        sub_water_management_areas['title'].append(
            'Sub-Water Management Areas')
        sub_water_management_areas['value'].append('???')

        sub_water_management_areas['title'].append(
            'Water Management Areas (WMA)')
        sub_water_management_areas['value'].append(water_management_areas)

        # Catchments
        if 'context_group_values' in context_document:
            if 'political_boundary_group' in context_document:
                province = self.parse_string(str(context_document
                                                 ['context_group_values']
                                                 ['political_boundary_group']
                                                 ['service_registry_values']
                                                 ['sa_provinces']
                                                 ['value']))
            else:
                province = 'Unknown'
        else:
            province = 'Unknown'

        sa_ecoregions['title'].append('Ecoregion Level 1')
        sa_ecoregions['value'].append('???')

        sa_ecoregions['title'].append('Ecoregion Level 2')
        sa_ecoregions['value'].append('???')

        sa_ecoregions['title'].append('Freshwater Ecoregion')
        sa_ecoregions['value'].append('???')

        sa_ecoregions['title'].append('Province')
        sa_ecoregions['value'].append(province)

        result = {}
        result['overview'] = overview
        result['catchments'] = catchments
        result['sub_water_management_areas'] = sub_water_management_areas
        result['sa_ecoregions'] = sa_ecoregions

        return result

    def parse_string(self, string_in):
        if not string_in:
            return 'Unknown'
        else:
            return string_in

    def get_number_of_records_and_taxa(self, records_collection):
        result = {}
        result['title'] = []
        result['value'] = []

        number_of_occurrence_records = 0
        taxonomy_list = []
        for each_record in records_collection:
            number_of_occurrence_records += 1
            taxonomy_id = each_record.taxonomy.id
            taxonomy_list.append(taxonomy_id)
        number_of_unique_taxa = len(set(taxonomy_list))

        result['title'].append('Number of occurrence records')
        result['value'].append(str(self.parse_string(
            number_of_occurrence_records)))
        result['title'].append('Number of species')
        result['value'].append(str(self.parse_string(number_of_unique_taxa)))

        return result

    def get_origin_data(self, records_collection):
        result = {}
        result['title'] = []
        result['value'] = []

        number_of_native = 0
        number_of_non_native = 0
        number_of_translocated = 0
        for each_record in records_collection:
            try:
                if str(each_record.category) == 'indigenous':
                    number_of_native += 1
                if str(each_record.category) == 'alien':
                    number_of_non_native += 1
                if str(each_record.category) == 'translocated':
                    number_of_translocated += 1
            except KeyError:
                pass

        result['title'].append('Native')
        result['value'].append(str(number_of_native))
        result['title'].append('Non-native')
        result['value'].append(str(number_of_non_native))
        result['title'].append('Translocated')
        result['value'].append(str(number_of_translocated))

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
