# coding=utf8
import ast
import csv
import json
import os
from collections import OrderedDict
import errno
from datetime import datetime
from hashlib import sha256

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Polygon
from django.db.models import Q, F, Count, Value, Case, When
from django.db.models.functions import ExtractYear
from django.http import Http404, JsonResponse, HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from sorl.thumbnail import get_thumbnail
from preferences import preferences

from bims.models.download_request import DownloadRequest
from bims.models.chemical_record import ChemicalRecord
from bims.models.location_site import LocationSite
from bims.models.location_context import LocationContext
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.models.biotope import Biotope
from bims.serializers.chemical_records_serializer import \
    ChemicalRecordsSerializer
from bims.serializers.location_site_serializer import (
    LocationSiteSerializer,
    LocationSitesCoordinateSerializer
)
from bims.serializers.location_site_detail_serializer import \
    LocationSiteDetailSerializer
from bims.api_views.collection import GetCollectionAbstract
from bims.utils.search_process import (
    get_or_create_search_process,
    create_search_process_file,
)
from bims.models.search_process import (
    SITES_SUMMARY,
    SEARCH_FINISHED,
)
from bims.api_views.search import CollectionSearch
from bims.models.iucn_status import IUCNStatus
from bims.models.site_image import SiteImage
from bims.models.taxon_group import TaxonGroup
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.models.survey import Survey
from bims.models.dashboard_configuration import DashboardConfiguration
from bims.models.taxonomy import Taxonomy
from bims.models.location_context_filter_group_order import (
    LocationContextFilterGroupOrder
)
from bims.tasks.email_csv import send_csv_via_email
from bims.tasks.collection_record import download_gbif_ids


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
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        context = {
            'collection_results': collection_results
        }
        location_site = self.get_object(site_id)
        serializer = LocationSiteDetailSerializer(
            location_site,
            context=context)
        return Response(serializer.data)


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
    CHEMICAL_RECORDS = 'chemical_records'
    SURVEY = 'survey'
    iucn_category = {}
    origin_name_list = {}

    def conservation_status_data(self, national, collection_results):
        if not national:
            cons_status_data = collection_results.filter(
                taxonomy__iucn_status__isnull=False
            )
        else:
            cons_status_data = collection_results.filter(
                taxonomy__national_conservation_status__isnull=False
            )
        cons_status_data = cons_status_data.annotate(
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
            if 'NE' in keys:
                key_index = keys.index('NE')
                values[key_index] += dd_values
            else:
                keys.append('NE')
                values.append(dd_values)
        return [keys, values]

    def generate(self, filters, search_process):
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        site_id = filters['siteId']

        self.iucn_category = dict(
            (x, y) for x, y in IUCNStatus.CATEGORY_CHOICES)

        self.origin_name_list = dict(
            (x, y) for x, y in Taxonomy.CATEGORY_CHOICES
        )

        taxa_occurrence = self.site_taxa_occurrences_per_year(
            collection_results)

        category_summary = collection_results.exclude(
            taxonomy__origin=''
        ).annotate(
            origin=F('taxonomy__origin')
        ).values_list(
            'origin'
        ).annotate(
            count=Count('taxonomy__origin')
        )
        is_multi_sites = False
        is_sass_exists = False

        if site_id:
            site_details = self.get_site_details(site_id)
            site_details['Species and Occurences'] = (
                self.get_number_of_records_and_taxa(collection_results))
        else:
            is_multi_sites = True
            site_details = self.multiple_site_details(collection_results)
            is_sass_exists = collection_results.filter(
                notes__icontains='sass'
            ).count() > 0
        search_process.set_search_raw_query(
            search.location_sites_raw_query
        )
        search_process.set_status(SEARCH_FINISHED, False)
        search_process.create_view()

        biodiversity_data = self.get_biodiversity_data(collection_results)
        site_images = []
        if not is_multi_sites:
            site_image_objects = SiteImage.objects.filter(
                Q(survey__in=list(
                    collection_results.distinct('survey').values_list(
                        'survey__id', flat=True))) |
                Q(site_id=int(site_id))
            ).values_list(
                'image', flat=True
            )
            for site_image in site_image_objects:
                site_images.append(
                    get_thumbnail(
                        site_image, 'x500', crop='center', quality=99).url
                )

        # Check module
        modules = []
        if 'modules' in filters:
            modules = list(TaxonGroup.objects.filter(
                category=TaxonomicGroupCategory.SPECIES_MODULE.name,
                id=filters['modules']
            ).values_list('name', flat=True))

        # - Survey
        survey_list = []
        surveys = Survey.objects.filter(
            id__in=collection_results.values('survey')
        ).order_by('-date')
        for survey in surveys[:5]:
            survey_list.append({
                'date': str(survey.date),
                'site': str(survey.site),
                'id': survey.id,
                'records': (
                    BiologicalCollectionRecord.objects.filter(
                        survey=survey).count()
                )
            })

        # - Source references
        collection_with_references = collection_results.exclude(
            source_reference__isnull=True
        ).distinct('source_reference')

        source_references = collection_with_references.source_references()

        # - Chemical data
        list_chems = {}
        chem_exist = False
        if site_id:
            list_chems_code = [
                'COND',
                'TEMP',
                'PH',
                'DO'
            ]
            chems = ChemicalRecord.objects.filter(
                Q(location_site_id=site_id) |
                Q(survey__site_id=site_id)
            )
            chems_source_references = chems.source_references()
            if chems_source_references:
                existing_ids = [
                    ref['ID'] for ref in source_references
                ]
                for chem_source_reference in chems_source_references:
                    if (
                            'ID' in chem_source_reference and
                            chem_source_reference['ID'] not in existing_ids
                    ):
                        source_references.append(chem_source_reference)
            x_label = []
            if chems.count() > 0:
                chem_exist = True
            for chem in list_chems_code:
                chem_name = chem.lower().replace('-n', '').upper()
                qs = chems.filter(chem__chem_code=chem).order_by('date')
                if not qs:
                    continue
                value = ChemicalRecordsSerializer(qs, many=True)
                # Get chemical unit
                chem_unit = qs[0].chem.chem_unit.unit
                data = {
                    'unit': chem_unit,
                    'name': qs[0].chem.chem_description,
                    'values': value.data
                }
                for val in value.data:
                    if val['str_date'] not in x_label:
                        x_label.append(val['str_date'])
                try:
                    list_chems[chem_name].append({chem: data})
                except KeyError:
                    list_chems[chem_name] = [{chem: data}]
            list_chems['x_label'] = x_label

        try:
            dashboard_configuration = json.loads(
                DashboardConfiguration.objects.get(
                    module_group__id=filters['modules']
                ).additional_data
            )
        except (
                DashboardConfiguration.DoesNotExist,
                KeyError,
                ValueError
        ):
            dashboard_configuration = {}

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
            self.CHEMICAL_RECORDS: list_chems,
            self.SURVEY: survey_list,
            'modules': modules,
            'site_images': list(site_images),
            'process': search_process.process_id,
            'extent': search.extent(),
            'sites_raw_query': search_process.process_id,
            'is_multi_sites': is_multi_sites,
            'is_sass_exists': is_sass_exists,
            'is_chem_exists': chem_exist,
            'total_survey': surveys.count(),
            'dashboard_configuration': dashboard_configuration,
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
            origin=Case(When(taxonomy__origin='',
                             then=Value('Unknown')),
                        default=F('taxonomy__origin')),
            cons_status=Case(
                            When(taxonomy__iucn_status__isnull=False,
                                  then=F('taxonomy__iucn_status__category')),
                             default=Value('Not evaluated')),
            cons_status_national=Case(
                            When(
                                taxonomy__national_conservation_status__isnull
                                =False,
                                then=F('taxonomy__iucn_status__category')),
                             default=Value('Not evaluated')),
            endemism=Case(When(taxonomy__endemism__isnull=False,
                               then=F('taxonomy__endemism__name')),
                          default=Value('Unknown')),
        ).values(
            'taxon', 'origin', 'cons_status',
            'cons_status_national', 'endemism'
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
        biodiversity_data['species']['biotope_chart'] = {}
        biodiversity_data['species']['cons_status_national_chart'] = {}
        origin_by_name_data = collection_results.annotate(
            name=Case(When(taxonomy__origin='',
                           then=Value('Unknown')),
                      default=F('taxonomy__origin'))
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

        biodiversity_data['species']['cons_status_chart']['data'] = self.conservation_status_data(
            False, collection_results)[1]
        biodiversity_data['species']['cons_status_chart']['keys'] = self.conservation_status_data(
            False, collection_results)[0]

        biodiversity_data['species']['cons_status_national_chart']['data'] = self.conservation_status_data(
            True, collection_results)[1]
        biodiversity_data['species']['cons_status_national_chart']['keys'] = self.conservation_status_data(
            True, collection_results)[0]
        endemism_status_data = collection_results.annotate(
            name=Case(When(taxonomy__endemism__name__isnull=False,
                           then=F('taxonomy__endemism__name')),
                      default=Value('Unknown'))
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
            smd_keys.append('Unknown')
        biodiversity_data['species']['sampling_method_chart'] = {
            'data': smd_data,
            'keys': smd_keys
        }

        # Biotope
        biotopes = Biotope.objects.filter(
            biologicalcollectionrecord__id__in=list(
                collection_results.values_list('id', flat=True)
            )
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        )
        biotope_keys = list(biotopes.values_list('name', flat=True))
        biotope_data = list(biotopes.values_list('count', flat=True))
        unspecified_biotope = collection_results.filter(
            biotope__isnull=True
        ).count()
        if unspecified_biotope > 0:
            biotope_data.append(unspecified_biotope)
            biotope_keys.append('Unknown')
        biodiversity_data['species']['biotope_chart'] = {
            'data': biotope_data,
            'keys': biotope_keys
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

        summary['overview']['Occurences'] = (
            collection_records.count()
        )
        summary['overview']['Number of Sites'] = (
            collection_records.distinct('site').count()
        )
        summary['overview']['Number of Taxa'] = (
            collection_records.distinct('taxonomy').count()
        )

        return summary

    def get_site_details(self, site_id):
        # get single site detailed dashboard overview data
        try:
            location_site = LocationSite.objects.get(id=site_id)
        except LocationSite.DoesNotExist:
            return {}
        location_context = LocationContext.objects.filter(site=location_site)
        site_river = '-'
        if location_site.river:
            site_river = location_site.river.name
        overview = dict()
        overview['{} Site Code'.format(
            preferences.SiteSetting.default_site_name
        )] = location_site.site_code
        overview['User Site Code'] = location_site.legacy_site_code
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

        result = dict()
        result['Overview'] = overview

        if preferences.SiteSetting.site_code_generator == 'fbis':
            river_and_geo = OrderedDict()
            river_and_geo['River'] = site_river
            river_and_geo[
                'User River Name'] = location_site.legacy_river_name
            river_and_geo['Geomorphological zone'] = (
                location_context.value_from_key(
                    'geo_class_recoded')
            )
            refined_geomorphological = '-'
            if location_site.refined_geomorphological:
                refined_geomorphological = (
                    location_site.refined_geomorphological
                )
            river_and_geo['Original Geomorphological zone'] = (
                refined_geomorphological
            )
            result['River and Geomorphological Zone'] = river_and_geo

        # Location context group data
        location_context_filters = (
            LocationContextFilterGroupOrder.objects.filter(
                show_in_dashboard=True
            ).order_by('group_display_order')
        )

        for context_filter in location_context_filters:
            title = context_filter.filter.title
            if title not in result:
                result[title] = {}
            result[title][context_filter.group.name] = (
                location_context.value_from_key(
                    context_filter.group.key
                )
            )

        return result

    def parse_string(self, string_in):
        if not string_in:
            return '-'
        else:
            if isinstance(string_in, str):
                return string_in.strip()
            return str(string_in)

    def get_number_of_records_and_taxa(self, records_collection):
        records_collection.annotate()
        result = dict()
        number_of_occurrence_records = records_collection.count()
        number_of_unique_taxa = records_collection.values(
            'taxonomy_id').distinct().count()
        result['Number of Occurrences'] = self.parse_string(
            number_of_occurrence_records)
        result['Number of Taxa'] = self.parse_string(number_of_unique_taxa)
        return result

    def get_origin_data(self, collection_results):
        origin_data = collection_results.annotate(
            value=F('taxonomy__origin')
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


def generate_gbif_ids_data(
        path_file,
        request,
        send_email=False,
        user_id=None
):
    def get_download_request(download_request_id):
        try:
            return DownloadRequest.objects.get(id=download_request_id)
        except DownloadRequest.DoesNotExist:
            return None

    filters = request
    headers = ['TAXON', 'GBIF SPECIES LINK', 'GBIF OCCURRENCE LINK']
    download_request_id = filters.get('downloadRequestId', '')
    download_request = None
    if download_request_id:
        try:
            download_request = DownloadRequest.objects.get(
                id=download_request_id
            )
        except DownloadRequest.DoesNotExist:
            pass

    if download_request and download_request.rejected:
        download_request.processing = False
        download_request.save()
        return False

    search = CollectionSearch(filters)
    collection_results = search.process_search()
    collection_results = collection_results.exclude(
        upstream_id=''
    )

    if collection_results.count() > 0:
        with open(path_file, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            total_records = collection_results.count()
            for index, record in enumerate(collection_results):
                writer.writerow({
                    'TAXON': record.taxonomy.canonical_name,
                    'GBIF SPECIES LINK': 'https://gbif.org/species/{0}'.format(
                        record.taxonomy.gbif_key),
                    'GBIF OCCURRENCE LINK': (
                        'https://gbif.org/occurrence/{}'.format(
                            record.upstream_id
                        )
                    )
                })

                download_request = get_download_request(download_request_id)
                if download_request and not download_request.rejected:
                    download_request.progress = (
                        f'{index + 1}/{total_records}'
                    )
                    download_request.save()
                elif download_request.rejected:
                    return False

    if download_request:
        download_request.processing = False
        download_request.request_file = path_file
        download_request.save()

    download_request = get_download_request(download_request_id)
    if (
        send_email and user_id and
        download_request and download_request.approved
    ):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(id=user_id)
            send_csv_via_email(
                user_id=user.id,
                csv_file=path_file,
                file_name='GBIFRecords',
                download_request_id=download_request_id
            )
        except UserModel.DoesNotExist:
            pass

    return True


class GbifIdsDownloader(APIView):

    def get_hashed_name(self, request):
        query_string = json.dumps(
            request.GET.dict()
        ) + datetime.today().strftime('%Y%m%d')
        return sha256(
            query_string.encode('utf-8')
        ).hexdigest()

    def get(self, request):
        filename = self.get_hashed_name(request)
        filename += '.csv'

        # Check if filename exists
        folder = settings.PROCESSED_CSV_PATH
        path_folder = os.path.join(settings.MEDIA_ROOT, folder)
        path_file = os.path.join(path_folder, filename)
        download_request_id = self.request.GET.get('downloadRequestId', '')

        try:
            os.mkdir(path_folder)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass

        try:
            download_request = DownloadRequest.objects.get(
                id=download_request_id
            )
        except DownloadRequest.DoesNotExist:
            return Response({
                'status': 'failed',
                'message': 'Download request does not exist'
            })

        if os.path.exists(path_file) and download_request.approved:
            send_csv_via_email.delay(
                user_id=self.request.user.id,
                csv_file=path_file,
                file_name='GBIFRecords',
                download_request_id=download_request_id
            )
        else:
            if os.path.exists(path_file):
                return Response({
                    'status': 'failed',
                    'message': 'Download request has been requested'
                })

            download_gbif_ids.delay(
                path_file,
                self.request.GET,
                send_email=True,
                user_id=self.request.user.id)

        return Response({
            'status': 'processing',
            'filename': filename
        })
