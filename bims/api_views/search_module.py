import operator
from functools import reduce

from django.contrib.gis.db.models.aggregates import Extent
from django.db.models.functions import Concat

from geonode.people.models import Profile
from bims.models.source_reference import LIST_SOURCE_REFERENCES
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Value

from bims.models.survey import Survey
from rest_framework import serializers

from bims.models.location_site import LocationSite
from rest_framework.response import Response

from bims.api_views.search import CollectionSearch
from bims.models.water_temperature import WaterTemperature
from bims.utils.api_view import BimsApiView


class SiteModuleSerializer(serializers.ModelSerializer):
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


class SearchModuleAPIView(BimsApiView):

    def get(self, request, *args):
        search = SearchModule(parameters=request.GET)
        search_result = search.get_summary_data()
        return Response(search_result)


class SearchModule(CollectionSearch):
    sites = None
    water_temperature = WaterTemperature.objects.all()
    survey = Survey.objects.none()

    def extent(self):
        # Get extent from collection results
        if self.water_temperature.count() < 1:
            return []
        extent = self.sites.aggregate(extent=Extent('geometry_point'))
        return list(extent['extent'])

    def run_search(self):
        if self.search_query:
            self.water_temperature = self.water_temperature.filter(
                location_site__site_code__icontains=self.search_query
            )
        if self.reference:
            self.water_temperature = self.water_temperature.filter(
                source_reference__in=self.reference
            )

        if self.year_ranges:
            self.water_temperature = self.water_temperature.filter(
                date_time__range=self.year_ranges
            )

        if self.months:
            self.water_temperature = self.water_temperature.filter(
                date_time__month__in=self.months
            )

        if self.reference_category:
            clauses = (
                Q(source_reference__polymorphic_ctype=
                    ContentType.objects.get_for_model(
                        LIST_SOURCE_REFERENCES[p])) for p in
                self.reference_category
            )
            reference_category_filter = reduce(operator.or_, clauses)
            self.water_temperature = self.water_temperature.filter(
                reference_category_filter
            )

        if self.collector:
            collectors = Profile.objects.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(full_name__in=self.collector)
            collector_list = list(collectors.values_list('id', flat=True))
            self.water_temperature = self.water_temperature.filter(
                owner__in=collector_list
            )

        self.sites = LocationSite.objects.filter(
            id__in=self.water_temperature.values('location_site')
        )

        spatial_filters = self.spatial_filter
        if spatial_filters:
            self.sites = self.sites.filter(
                spatial_filters
            )

    def get_summary_data(self):
        self.run_search()
        return {
            'total': 0,
            'total_survey': 0,
            'total_sites': self.sites.count(),
            'sites': SiteModuleSerializer(
                self.sites,
                many=True,
                context={
                    'water_temperature': self.water_temperature
                }
            ).data
        }
