import hashlib
import json
from collections import OrderedDict

from bims.models.search_process import SITES_SUMMARY, SEARCH_PROCESSING

from bims.models.water_temperature import WaterTemperature
from django.db.models import F, Value, Case, When, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from sorl.thumbnail import get_thumbnail
from django.http import Http404
from bims.api_views.search import CollectionSearch
from bims.models import (
    TaxonGroup,
    Taxonomy,
    IUCNStatus, ChemicalRecord,
)
from bims.enums import TaxonomicGroupCategory
from bims.tasks import location_sites_overview
from bims.utils.api_view import BimsApiView
from bims.utils.search_process import get_or_create_search_process
from sass.models.site_visit_taxon import SiteVisitTaxon
from bims.models.location_site import LocationSite
from bims.serializers.location_site_detail_serializer import (
    LocationSiteDetailSerializer,
)


class LocationSiteOverviewData(object):
    BIODIVERSITY_DATA = 'biodiversity_data'
    MODULE = 'module'
    SASS_EXIST = 'sass_exist'
    GROUP_ICON = 'icon'
    GROUP_OCCURRENCES = 'occurrences'
    GROUP_SITES = 'sites'
    GROUP_ENDEMISM = 'endemism'
    GROUP_NUM_OF_TAXA = 'number_of_taxa'
    GROUP_ORIGIN = 'origin'
    GROUP_CONS_STATUS = 'cons_status'
    WATER_TEMPERATURE_EXIST = 'water_temperature_exist'
    WATER_TEMPERATURE_DATA = 'water_temperature_data'
    PHYSICO_CHEMICAL_EXIST = 'physico_chemical_exist'

    search_filters = None
    is_sass_exist = False

    def biodiversity_data(self):
        if not self.search_filters:
            return {}
        search = CollectionSearch(self.search_filters)
        collection_results = search.process_search()

        biodiversity_data = OrderedDict()

        groups = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        ).order_by('display_order')

        for group in groups:
            group_data = dict()
            try:
                group_data[self.GROUP_ICON] = get_thumbnail(
                    group.logo, 'x50', crop='center'
                ).name
            except ValueError:
                pass
            group_data[self.MODULE] = group.id

            biodiversity_data[group.name] = group_data
            group_records = collection_results.filter(
                module_group=group
            )

            if group_records.count() > 0 and not self.is_sass_exist:
                try:
                    if isinstance(
                            collection_results.first(),
                            SiteVisitTaxon):
                        self.is_sass_exist = group_records.filter(
                            site_visit__isnull=False
                        ).count() > 0
                    else:
                        self.is_sass_exist = group_records.filter(
                            sitevisittaxon__isnull=False
                        ).count() > 0
                except:  # noqa
                    self.is_sass_exist = False

            group_data[self.GROUP_OCCURRENCES] = group_records.count()
            group_data[self.GROUP_SITES] = LocationSite.objects.filter(
                id__in=group_records.values('site')
            ).count()
            group_data[self.GROUP_NUM_OF_TAXA] = Taxonomy.objects.filter(
                id__in=group_records.values('taxonomy')
            ).count()
            group_data[self.GROUP_ENDEMISM] = list(group_records.annotate(
                name=Case(When(taxonomy__endemism__isnull=False,
                               then=F('taxonomy__endemism__name')),
                          default=Value('Unknown'))
            ).values(
                'name'
            ).annotate(
                count=Count('name')
            ).values(
                'name', 'count'
            ).order_by('name'))

            group_origins = group_records.annotate(
                name=Case(When(taxonomy__origin='',
                               then=Value('Unknown')),
                          default=F('taxonomy__origin'))
            ).values(
                'name'
            ).annotate(
                count=Count('name')
            ).values(
                'name', 'count'
            ).order_by('name')
            if group_origins:
                category = dict(Taxonomy.CATEGORY_CHOICES)
                for group_origin in group_origins:
                    if group_origin['name'] in category:
                        group_origin['name'] = category[group_origin['name']]
            group_data[self.GROUP_ORIGIN] = list(group_origins)

            all_cons_status = group_records.annotate(
                name=Case(When(taxonomy__iucn_status__isnull=False,
                               then=F('taxonomy__iucn_status__category')),
                          default=Value('Not evaluated'))
            ).values(
                'name'
            ).annotate(
                count=Count('name')
            ).values(
                'name', 'count'
            ).order_by('name')
            if all_cons_status:
                category = dict(IUCNStatus.CATEGORY_CHOICES)
                for cons_status in all_cons_status:
                    if cons_status['name'] in category:
                        cons_status['name'] = category[cons_status['name']]
            group_data[self.GROUP_CONS_STATUS] = list(all_cons_status)

        return biodiversity_data


class MultiLocationSitesOverview(APIView, LocationSiteOverviewData):

    def get(self, request):
        """
        Get overview data for multiple sites
        """
        self.search_filters = request.GET

        response_data = dict()
        response_data[self.BIODIVERSITY_DATA] = self.biodiversity_data()
        response_data[self.SASS_EXIST] = self.is_sass_exist
        return Response(response_data)


class MultiLocationSitesBackgroundOverview(BimsApiView):
    def get(self, request):
        parameters = request.GET
        search_uri = request.build_absolute_uri()

        search_process, created = get_or_create_search_process(
            search_type=SITES_SUMMARY,
            query=search_uri
        )
        results = search_process.get_file_if_exits()
        if results:
            return Response(results)

        data_for_process_id = dict()
        data_for_process_id['search_uri'] = search_uri

        process_id = hashlib.sha256(
            str(
                json.dumps(
                    data_for_process_id, sort_keys=True
                )
            ).encode('utf-8')
        ).hexdigest()

        search_process.set_process_id(process_id)
        search_process.set_status(SEARCH_PROCESSING)

        task = location_sites_overview.delay(
            search_parameters=parameters,
            search_process_id=search_process.id
        )

        result_file = search_process.get_file_if_exits(
            finished=False
        )
        if result_file:
            result_file['task_id'] = task.id
            return Response(result_file)

        return Response({'status': 'Process does not exists'})


class SingleLocationSiteOverview(APIView, LocationSiteOverviewData):

    def get_object(self, pk):
        try:
            return LocationSite.objects.get(pk=pk)
        except LocationSite.DoesNotExist:
            raise Http404

    def get(self, request):
        self.search_filters = request.GET
        response_data = dict()
        response_data[self.BIODIVERSITY_DATA] = self.biodiversity_data()
        response_data[self.SASS_EXIST] = self.is_sass_exist

        site_id = request.GET.get('siteId')
        location_site = self.get_object(site_id)
        response_data[self.WATER_TEMPERATURE_EXIST] = (
            WaterTemperature.objects.filter(
                location_site=location_site
            ).exists()
        )
        response_data[self.PHYSICO_CHEMICAL_EXIST] = (
            ChemicalRecord.objects.filter(
                Q(location_site=location_site) |
                Q(survey__site=location_site)
            ).exists()
        )
        serializer = LocationSiteDetailSerializer(
            location_site)
        response_data.update(serializer.data)
        return Response(response_data)
