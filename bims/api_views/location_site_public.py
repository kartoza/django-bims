# coding=utf8
from collections import OrderedDict
from django.db.models import Q, F, Count, Value, Case, When
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from sorl.thumbnail import get_thumbnail
from preferences import preferences
from bims.models.chemical_record import ChemicalRecord
from bims.models.location_site import LocationSite
from bims.models.location_context import LocationContext
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.serializers.chemical_records_serializer import \
    ChemicalRecordsSerializer

from bims.api_views.search import CollectionSearch
from bims.models.iucn_status import IUCNStatus
from bims.models.site_image import SiteImage
from bims.models.taxon_group import TaxonGroup
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from sass.enums.chem_unit import ChemUnit
from bims.models.survey import Survey
from bims.models.taxonomy import Taxonomy
from bims.models.location_context_filter_group_order import (
    LocationContextFilterGroupOrder
)
from bims.request_log.mixin import RequestLogViewMixin


class LocationSiteSummaryPublic(RequestLogViewMixin, APIView):
    """
        List cached location site summary based on collection record search.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    COUNT = 'count'
    ORIGIN = 'origin'
    TOTAL_RECORDS = 'total_occurrences'
    TOTAL_SURVEY = 'total_site_visits'
    TAXA_OCCURRENCE = 'taxa_occurrence'
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
    ERROR_MESSAGE = 'error_message'
    SURVEY = 'site_visit'
    MODULES = 'modules'
    SITE_IMAGES = 'site_images'
    iucn_category = {}
    origin_name_list = {}

    def generate(self, filters):
        site_id = filters['siteId']

        if not site_id:
            return {
                self.ERROR_MESSAGE: 'Site id not found'
            }

        if ',' in site_id:
            return {
                self.ERROR_MESSAGE: 'Only supports single site'
            }

        if not LocationSite.objects.filter(id=site_id):
            return {
                self.ERROR_MESSAGE: 'Site not found'
            }

        search = CollectionSearch(filters)
        collection_results = search.process_search()

        self.iucn_category = dict(
            (x, y) for x, y in IUCNStatus.CATEGORY_CHOICES)

        self.origin_name_list = dict(
            (x, y) for x, y in Taxonomy.CATEGORY_CHOICES
        )

        site_details = self.get_site_details(site_id)
        site_details['Species and Occurences'] = (
            self.get_number_of_records_and_taxa(collection_results))

        site_image_objects = SiteImage.objects.filter(
            Q(survey__in=list(
                collection_results.distinct('survey').values_list(
                    'survey__id', flat=True))) |
            Q(site_id=int(site_id))
        ).values_list(
            'image', flat=True
        )
        site_images = []
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
            for chem in list_chems_code:
                chem_name = chem.lower().replace('-n', '').upper()
                qs = chems.filter(chem__chem_code=chem).order_by('date')
                if not qs:
                    continue
                value = ChemicalRecordsSerializer(qs, many=True)
                # Get chemical unit
                try:
                    chem_unit = ChemUnit[qs[0].chem.chem_unit].value
                except KeyError:
                    chem_unit = qs[0].chem.chem_unit
                data = {
                    'unit': chem_unit,
                    'name': qs[0].chem.chem_description,
                    'values': value.data
                }
                try:
                    list_chems[chem_name].append({chem: data})
                except KeyError:
                    list_chems[chem_name] = [{chem: data}]

        response_data = {
            self.TOTAL_RECORDS: collection_results.count(),
            self.TOTAL_SURVEY: surveys.count(),
            self.SITE_DETAILS: dict(site_details),
            self.OCCURRENCE_DATA: self.occurrence_data(collection_results),
            self.SOURCE_REFERENCES: source_references,
            self.CHEMICAL_RECORDS: list_chems,
            self.SURVEY: survey_list,
            self.MODULES: modules,
            self.SITE_IMAGES: list(site_images),
        }
        return response_data

    def occurrence_data(self, collection_results):
        """
        Get occurrence data
        :param collection_results: collection search results
        :return: list of occurrence data
        """
        occurrence_table_data = collection_results.annotate(
            taxon=F('taxonomy__scientific_name'),
            site_visit_id=F('survey_id'),
            origin=Case(When(category='',
                             then=Value('Unknown')),
                        default=F('category')),
            cons_status=Case(When(taxonomy__iucn_status__isnull=False,
                                  then=F('taxonomy__iucn_status__category')),
                             default=Value('Not evaluated')),
            endemism=Case(When(taxonomy__endemism__isnull=False,
                               then=F('taxonomy__endemism__name')),
                          default=Value('Unknown')),
        ).values(
            'taxon', 'collection_date', 'origin', 'cons_status',
            'endemism', 'site_visit_id'
        ).annotate(
            count=Count('taxon')
        ).order_by('taxon')
        occurrence_data = []

        for table_data in occurrence_table_data:
            try:
                table_data['origin'] = (
                    self.origin_name_list[table_data['origin']]
                )
                table_data['cons_status'] = (
                    self.iucn_category[table_data['cons_status']]
                )
            except KeyError:
                pass
            occurrence_data.append(table_data)

        return occurrence_data


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
        overview['Original Site Code'] = location_site.legacy_site_code
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
                'Original River Name'] = location_site.legacy_river_name
            river_and_geo['Geomorphological zone'] = (
                location_context.value_from_key(
                    'geo_class_recoded')
            )
            refined_geomorphological = '-'
            if location_site.refined_geomorphological:
                refined_geomorphological = (
                    location_site.refined_geomorphological
                )
            river_and_geo['Refined Geomorphological zone'] = (
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
        return Response(self.generate(
            request.GET.dict()
        ))
