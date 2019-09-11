# coding=utf8
import ast
import json
import os
from django.contrib.gis.geos import Polygon
from django.db.models import Q, F, Count, Value, Case, When
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
    create_search_process_file,
)
from bims.models.search_process import (
    SITES_SUMMARY,
    SEARCH_FINISHED,
)
from bims.api_views.search import Search
from bims.models.iucn_status import IUCNStatus
from bims.models.site_image import SiteImage
from bims.models.taxon_group import TaxonGroup
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


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
        filters = request.GET

        # Search collection
        search = Search(filters)
        collection_results = search.process_search()
        context = {
            'collection_results': collection_results
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
    TAXA_OCCURRENCE = 'taxa_occurrence'
    CATEGORY_SUMMARY = 'category_summary'
    TAXONOMY_NAME = 'name'
    BIODIVERSITY_DATA = 'biodiversity_data'
    SITE_DETAILS = 'site_details'
    OCCURRENCE_DATA = 'occurrence_data'
    IUCN_NAME_LIST = 'iucn_name_list'
    ORIGIN_NAME_LIST = 'origin_name_list'
    TAXA_GRAPH = 'taxa_graph'
    ORIGIN_OCCURRENCE = 'origin_occurrence'
    CONS_STATUS_OCCURRENCE = 'cons_status_occurrence'
    SOURCE_REFERENCES = 'source_references'
    iucn_category = {}
    origin_name_list = {}

    def generate(self, filters, search_process):
        search = Search(filters)
        collection_results = search.process_search()
        site_id = filters['siteId']

        self.iucn_category = dict(
            (x, y) for x, y in IUCNStatus.CATEGORY_CHOICES)

        self.origin_name_list = dict(
            (x, y) for x, y in BiologicalCollectionRecord.CATEGORY_CHOICES
        )

        taxa_occurrence = self.site_taxa_occurrences_per_year(
            collection_results)

        category_summary = collection_results.filter(
            category__isnull=False
        ).annotate(
            origin=F('category')
        ).values_list(
            'origin'
        ).annotate(
            count=Count('category')
        )
        is_multi_sites = False
        is_sass_exists = False

        if site_id:
            site_details = self.get_site_details(site_id)
            site_details['records_and_sites'] = (
                self.get_number_of_records_and_taxa(collection_results))
        else:
            is_multi_sites = True
            site_details = self.multiple_site_details(collection_results)
            is_sass_exists = collection_results.filter(
                notes__icontains='sass'
            ).exists()
        search_process.set_search_raw_query(
            search.location_sites_raw_query
        )
        search_process.set_status(SEARCH_FINISHED, False)

        search_process.create_view()
        biodiversity_data = self.get_biodiversity_data(collection_results)
        site_images = SiteImage.objects.filter(
            site__in=list(
                collection_results.distinct('site').values_list(
                    'site__id', flat=True))).values_list(
            'image', flat=True
        )

        # Check module
        modules = []
        if 'modules' in filters:
            modules = list(TaxonGroup.objects.filter(
                category=TaxonomicGroupCategory.SPECIES_MODULE.name,
                id=filters['modules']
            ).values_list('name', flat=True))

        collection_with_references = collection_results.exclude(
            source_reference__isnull=True
        ).distinct('source_reference')
        source_references = [
            col.source_reference.link_template() for col in
            collection_with_references
        ]

        response_data = {
            self.TOTAL_RECORDS: collection_results.count(),
            self.SITE_DETAILS: dict(site_details),
            self.TAXA_OCCURRENCE: dict(taxa_occurrence),
            self.CATEGORY_SUMMARY: dict(category_summary),
            self.OCCURRENCE_DATA: self.occurrence_data(collection_results),
            self.IUCN_NAME_LIST: self.iucn_category,
            self.ORIGIN_NAME_LIST: self.origin_name_list,
            self.BIODIVERSITY_DATA: dict(biodiversity_data),
            self.SOURCE_REFERENCES: source_references,
            'modules': modules,
            'site_images': list(site_images),
            'process': search_process.process_id,
            'extent': search.extent(),
            'sites_raw_query': search_process.process_id,
            'is_multi_sites': is_multi_sites,
            'is_sass_exists': is_sass_exists
        }
        create_search_process_file(
            response_data, search_process, file_path=None, finished=True)
        return response_data

    def occurrence_data(self, collection_results):
        """
        Get occurrence data
        :param collection_results: collection search results
        :return: list of occurrence data
        """
        occurrence_table_data = collection_results.annotate(
            taxon=F('taxonomy__scientific_name'),
            origin=Case(When(category__isnull=False,
                             then=F('category')),
                        default=Value('Unspecified')),
            cons_status=F('taxonomy__iucn_status__category'),
            endemism=Case(When(taxonomy__endemism__isnull=False,
                               then=F('taxonomy__endemism__name')),
                          default=Value('Unspecified')),
        ).values(
            'taxon', 'origin', 'cons_status', 'endemism'
        ).annotate(
            count=Count('taxon')
        ).order_by('taxon')
        occurrence_data = list(occurrence_table_data)
        return occurrence_data

    def site_taxa_occurrences_per_year(self, collection_results):
        """
        Get occurrence data for charts
        :param: collection_records: collection record queryset
        :return: dict of taxa occurrence data for stacked bar graph
        """
        taxa_occurrence_data = collection_results.annotate(
            year=ExtractYear('collection_date'),
        ).values('year'
                 ).annotate(count=Count('year')
                            ).values('year', 'count'
                                     ).order_by('year')
        result = dict()
        result['occurrences_line_chart'] = {}
        result['occurrences_line_chart']['values'] = list(
            taxa_occurrence_data.values_list('count', flat=True))
        result['occurrences_line_chart']['keys'] = list(
            taxa_occurrence_data.values_list('year', flat=True))
        result['occurrences_line_chart']['title'] = 'Occurrences'
        return result

    def get_biodiversity_data(self, collection_results):
        biodiversity_data = {}
        biodiversity_data['species'] = {}
        biodiversity_data['species']['origin_chart'] = {}
        biodiversity_data['species']['cons_status_chart'] = {}
        biodiversity_data['species']['endemism_chart'] = {}
        biodiversity_data['species']['sampling_method_chart'] = {}
        origin_by_name_data = collection_results.annotate(
            name=Case(When(category__isnull=False,
                           then=F('category')),
                      default=Value('Unspecified'))
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )
        keys = origin_by_name_data.values_list('name', flat=True)
        values = origin_by_name_data.values_list('count', flat=True)
        biodiversity_data['species']['origin_chart']['data'] = list(values)
        biodiversity_data['species']['origin_chart']['keys'] = list(keys)
        cons_status_data = collection_results.filter(
            taxonomy__iucn_status__isnull=False
        ).annotate(
            name=F('taxonomy__iucn_status__category')
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )

        keys = list(cons_status_data.values_list('name', flat=True))
        values = list(cons_status_data.values_list('count', flat=True))
        dd_values = collection_results.filter(
            taxonomy__iucn_status__isnull=True
        ).count()
        if dd_values > 0:
            if 'DD' in keys:
                key_index = keys.index('DD')
                values[key_index] += dd_values
            else:
                keys.append('DD')
                values.append(dd_values)
        biodiversity_data['species']['cons_status_chart']['data'] = values
        biodiversity_data['species']['cons_status_chart']['keys'] = keys

        endemism_status_data = collection_results.annotate(
            name=Case(When(taxonomy__endemism__name__isnull=False,
                           then=F('taxonomy__endemism__name')),
                      default=Value('Unspecified'))
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )
        keys = endemism_status_data.values_list('name', flat=True)
        values = endemism_status_data.values_list('count', flat=True)
        biodiversity_data['species']['endemism_chart']['data'] = list(values)
        biodiversity_data['species']['endemism_chart']['keys'] = list(keys)

        # Sampling method
        sampling_method_data = collection_results.filter(
            sampling_method__isnull=False
        ).annotate(
            name=F('sampling_method__sampling_method')
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )
        smd_keys = list(sampling_method_data.values_list('name', flat=True))
        smd_data = list(sampling_method_data.values_list('count', flat=True))
        unspecified_sampling_method = collection_results.filter(
            sampling_method__isnull=True
        ).count()
        if unspecified_sampling_method > 0:
            smd_data.append(unspecified_sampling_method)
            smd_keys.append('Unspecified')
        biodiversity_data['species']['sampling_method_chart'] = {
            'data': smd_data,
            'keys': smd_keys
        }

        return biodiversity_data

    def multiple_site_details(self, collection_records):
        """
        Get detail overview for multiple site
        :param collection_records: biological colleciton records
        :return: dict of details
        """
        summary = {
            'overview': {}
        }

        summary['overview']['Number of Occurrence Records'] = (
            collection_records.count()
        )
        summary['overview']['Number of Sites'] = (
            collection_records.distinct('site').count()
        )
        summary['overview']['Number of Species'] = (
            collection_records.distinct('taxonomy').count()
        )

        return summary

    def get_site_details(self, site_id):
        # get single site detailed dashboard overview data
        try:
            location_site = LocationSite.objects.get(id=site_id)
        except LocationSite.DoesNotExist:
            return {}
        try:
            context_document = json.loads(location_site.location_context)
        except ValueError:
            context_document = {}
        site_river = '-'
        if location_site.river:
            site_river = location_site.river.name
        overview = dict()
        overview['FBIS Site Code'] = location_site.site_code
        overview['Site coordinates'] = (
            'Longitude: {long}, Latitude: {lat}'.format(
                long=self.parse_string(location_site.longitude),
                lat=self.parse_string(location_site.latitude)
            )
        )
        if location_site.site_description:
            overview['Site description'] = self.parse_string(
                location_site.site_description
            )
        else:
            overview['Site description'] = self.parse_string(
                location_site.name
            )

        river_and_geo = dict()
        river_and_geo['River'] = site_river

        try:
            eco_region = (
                context_document
                ['context_group_values']
                ['river_ecoregion_group']
                ['service_registry_values']
                ['eco_region_1']
                ['value'])
        except KeyError:
            eco_region = '-'
        try:
            geo_class = (
                context_document
                ['context_group_values']
                ['geomorphological_group']
                ['service_registry_values']
                ['geo_class_recoded']
                ['value'])
        except KeyError:
            geo_class = '-'
        try:
            geo_zone = ('{geo_class}'.format(
                geo_class=geo_class))
        except KeyError:
            geo_zone = '-'
        river_and_geo['Geomorphological zone'] = geo_zone

        refined_geomorphological = '-'
        if location_site.refined_geomorphological:
            refined_geomorphological = location_site.refined_geomorphological
        river_and_geo['Refined Geomorphological zone'] = \
            refined_geomorphological

        # Catchments
        catchments = dict()
        try:
            primary_catchment = (
                context_document
                ['context_group_values']
                ['river_catchment_areas_group']
                ['service_registry_values']
                ['primary_catchment_area']
                ['value'])
        except KeyError:
            primary_catchment = '-'
        try:
            secondary_catchment = (
                context_document
                ['context_group_values']
                ['river_catchment_areas_group']
                ['service_registry_values']
                ['secondary_catchment_area']
                ['value'])
        except KeyError:
            secondary_catchment = '-'
        try:
            tertiary_catchment_area = (
                context_document
                ['context_group_values']
                ['river_catchment_areas_group']
                ['service_registry_values']
                ['tertiary_catchment_area']
                ['value'])
        except KeyError:
            tertiary_catchment_area = '-'
        try:
            quaternary_catchment_area = (
                context_document
                ['context_group_values']
                ['river_catchment_areas_group']
                ['service_registry_values']
                ['quaternary_catchment_area']
                ['value'])
        except KeyError:
            quaternary_catchment_area = '-'
        try:
            water_management_area = (
                context_document
                ['context_group_values']
                ['water_management_area']
                ['service_registry_values']
                ['water_management_area']
                ['value'])
        except KeyError:
            water_management_area = '-'

        try:
            sub_water_management_area = (
                context_document
                ['context_group_values']
                ['water_management_area']
                ['service_registry_values']
                ['sub_wmas']
                ['value'])
        except KeyError:
            sub_water_management_area = '-'

        catchments['Primary'] = primary_catchment
        catchments['Secondary'] = secondary_catchment
        catchments['Tertiary'] = tertiary_catchment_area
        catchments['Quaternary'] = quaternary_catchment_area
        catchments['Quinary'] = '-'

        sub_water_management_areas = dict()
        sub_water_management_areas['Water Management Areas'] = (
            water_management_area
        )
        sub_water_management_areas['Sub Water Management Areas'] = (
            sub_water_management_area
        )
        sub_water_management_areas['River Management Unit'] = '-'

        # Politcal Boundary Group
        sa_ecoregions = dict()
        try:
            province = self.parse_string(str(context_document
                                             ['context_group_values']
                                             ['political_boundary_group']
                                             ['service_registry_values']
                                             ['sa_provinces']
                                             ['value']))
        except KeyError:
            province = '-'

        try:
            eco_region = self.parse_string(str(context_document
                                               ['context_group_values']
                                               ['river_ecoregion_group']
                                               ['service_registry_values']
                                               ['eco_region_1']
                                               ['value']))
        except KeyError:
            eco_region = '-'

        try:
            eco_region_2 = self.parse_string(str(context_document
                                                 ['context_group_values']
                                                 ['river_ecoregion_group']
                                                 ['service_registry_values']
                                                 ['eco_region_2']
                                                 ['value']))
        except KeyError:
            eco_region_2 = '-'

        try:
            freshwater_ecoregion = self.parse_string(
                context_document['context_group_values']
                ['freshwater_ecoregion_of_the_world']
                ['service_registry_values']
                ['feow_hydrosheds']
                ['value']
            )
        except KeyError:
            freshwater_ecoregion = '-'

        sa_ecoregions['SA Ecoregion Level 1'] = eco_region
        sa_ecoregions['SA Ecoregion Level 2'] = eco_region_2
        sa_ecoregions['Freshwater Ecoregion'] = freshwater_ecoregion
        sa_ecoregions['Province'] = province

        result = dict()
        result['overview'] = overview
        result['river_and_geomorphological'] = river_and_geo
        result['catchments'] = catchments
        result['sub_water_management_areas'] = sub_water_management_areas
        result['sa_ecoregions'] = sa_ecoregions

        return result

    def parse_string(self, string_in):
        if not string_in:
            return '-'
        else:
            return str(string_in)

    def get_number_of_records_and_taxa(self, records_collection):
        records_collection.annotate()
        result = dict()
        number_of_occurrence_records = records_collection.count()
        number_of_unique_taxa = records_collection.values(
            'taxonomy_id').distinct().count()
        result['Number of Occurrences'] = self.parse_string(
            number_of_occurrence_records)
        result['Number of Species'] = self.parse_string(number_of_unique_taxa)
        return result

    def get_origin_data(self, collection_results):
        origin_data = collection_results.annotate(
            value=F('category')
        ).values(
            'value'
        ).annotate(
            count=Count('value')
        ).order_by('value')
        return dict(origin_data.values_list('value', 'count'))

    def get_conservation_status_data(self, collection_results):
        iucn_data = collection_results.exclude(
            taxonomy__iucn_status__category=None).annotate(
            value=F('taxonomy__iucn_status__category')
        ).values(
            'value'
        ).annotate(
            count=Count('value'))
        return dict(iucn_data.values_list('value', 'count'))

    def get_value_or_zero_from_key(self, data, key):
        result = {}
        result['value'] = 0
        try:
            return str(data[key]['value'])
        except KeyError:
            return str(0)

    def get(self, request):
        filters = request.GET.dict()
        search_uri = request.build_absolute_uri()
        use_cached = ast.literal_eval(filters.get('cached', 'True'))

        search_process, created = get_or_create_search_process(
            SITES_SUMMARY,
            query=search_uri
        )

        if search_process.file_path and use_cached:
            if os.path.exists(search_process.file_path):
                try:
                    raw_data = open(search_process.file_path)
                    return Response(json.load(raw_data))
                except ValueError:
                    pass

        return Response(self.generate(
            filters,
            search_process
        ))


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
