import operator
from functools import reduce

from django.contrib.gis.db.models.aggregates import Extent
from django.db.models.functions import Concat

from geonode.people.models import Profile
from bims.models.source_reference import LIST_SOURCE_REFERENCES
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Value, F

from bims.models.survey import Survey
from rest_framework import serializers

from bims.models.location_site import LocationSite
from rest_framework.response import Response

from bims.api_views.search import CollectionSearch, MAX_PAGINATED_SITES
from bims.models.water_temperature import WaterTemperature
from bims.utils.api_view import BimsApiView
from bims.models.chemical_record import ChemicalRecord


class SiteWaterTemperatureSerializer(serializers.ModelSerializer):
    site_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    total_water_temperature_data = serializers.SerializerMethodField()

    def get_total_water_temperature_data(self, obj: LocationSite) -> int:
        return self.context['water_temperature'].filter(
            location_site=obj
        ).count()

    def get_site_id(self, obj: LocationSite) -> int:
        return obj.id

    def get_name(self, obj: LocationSite) -> str:
        return obj.site_code if obj.site_code else obj.name

    class Meta:
        model = LocationSite
        fields = [
            'site_id', 'name', 'total_water_temperature_data'
        ]


class SitePhysicoChemistrySerializer(serializers.ModelSerializer):
    site_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    total_chemical_records = serializers.SerializerMethodField()

    def get_total_chemical_records(self, obj: LocationSite) -> int:
        return self.context['chemical_records'].filter(
            location_site=obj
        ).count()

    def get_site_id(self, obj: LocationSite) -> int:
        return obj.id

    def get_name(self, obj: LocationSite) -> str:
        return obj.site_code if obj.site_code else obj.name

    class Meta:
        model = LocationSite
        fields = [
            'site_id', 'name', 'total_chemical_records'
        ]


class SearchModuleAPIView(BimsApiView):

    def get(self, request, *args):
        search = SearchModule(parameters=request.GET)
        search_result = search.get_summary_data()
        return Response(search_result)


class SearchModule(CollectionSearch):
    sites = None
    module = None
    survey = Survey.objects.none()
    date_field = 'date_time'

    def extent(self):
        # Get extent from collection results
        if self.module.count() < 1:
            return []
        extent = self.sites.aggregate(extent=Extent('geometry_point'))
        if 'extent' in extent and extent['extent']:
            return list(extent['extent'])
        return []

    def run_search(self):
        if self.search_query:
            self.module = self.module.filter(
                location_site__site_code__icontains=self.search_query
            )
        if self.reference:
            self.module = self.module.filter(
                source_reference__in=self.reference
            )

        if self.year_ranges:
            self.module = self.module.filter(**{
                f'{self.date_field}__range': self.year_ranges
            })

        if self.months:
            self.module = self.module.filter(**{
                f'{self.date_field}__month__in': self.months
            })

        if self.reference_category:
            clauses = (
                Q(source_reference__polymorphic_ctype=
                    ContentType.objects.get_for_model(
                        LIST_SOURCE_REFERENCES[p])) for p in
                self.reference_category
            )
            reference_category_filter = reduce(operator.or_, clauses)
            self.module = self.module.filter(
                reference_category_filter
            )

        if self.collector:
            collectors = Profile.objects.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(full_name__in=self.collector)
            collector_list = list(collectors.values_list('id', flat=True))
            self.module = self.module.filter(
                owner__in=collector_list
            )

        self.sites = LocationSite.objects.filter(
            id__in=list(
                self.module.exclude(location_site__isnull=True).values_list(
                    'location_site__id', flat=True
                )
            )
        )

        spatial_filters = self.spatial_filter
        if spatial_filters:
            self.sites = self.sites.filter(
                spatial_filters
            )

        if self.sites and not self.location_sites_raw_query:
            self.location_sites_raw_query = self.sites.annotate(
                site_id=F('id')
            ).values(
                'site_id',
                'geometry_point',
                'name'
            ).query.sql_with_params()

    def serialize_sites(self):
        return []

    def get_summary_data(self):
        self.run_search()

        # Get order_by
        order_by = self.get_request_data('orderBy', 'name')
        valid_order = [
            'total', '-total', 'name', '-name', 'total_survey', '-total_survey'
        ]
        if order_by not in valid_order:
            order_by = 'name'

        self.sites = self.sites.order_by(order_by)
        total = self.module.count() if self.module else 0
        if self.sites.count() == 0:
            total = 0

        return {
            'total': total,
            'total_survey': 0,
            'total_sites': self.sites.count(),
            'sites': self.serialize_sites()
        }


class WaterTemperatureModule(SearchModule):
    module = WaterTemperature.objects.all()

    def serialize_sites(self):
        return SiteWaterTemperatureSerializer(
            self.sites,
            many=True,
            context={
                'water_temperature': self.module
            }
        ).data


class PhysicoChemistryModule(SearchModule):
    module = ChemicalRecord.objects.all()
    date_field = 'date'

    def serialize_sites(self):
        return SitePhysicoChemistrySerializer(
            self.sites,
            many=True,
            context={
                'chemical_records': self.module
            }
        ).data
