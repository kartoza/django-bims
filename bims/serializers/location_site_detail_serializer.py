from rest_framework import serializers
from bims.models.location_site import LocationSite
from bims.models.location_context import LocationContext
from bims.serializers.location_site_serializer import LocationSiteSerializer
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.location_context_filter_group_order import (
    LocationContextFilterGroupOrder
)


class LocationSiteDetailSerializer(LocationSiteSerializer):
    """
    Serializer for location site detail.
    """
    geometry = serializers.SerializerMethodField()
    location_context = serializers.SerializerMethodField()

    def get_geometry(self, obj):
        geometry = obj.get_geometry()
        if geometry:
            return obj.get_geometry().json
        return ''

    def get_location_context(self, obj):
        context_data = {}
        filter_groups = (
            LocationContextFilterGroupOrder.objects.filter(
                show_in_side_panel=True
            ).order_by('group_display_order')
        )
        for filter_group in filter_groups:
            if filter_group.group.name not in context_data:
                context_data[filter_group.group.name] = (
                    LocationContext.objects.filter(
                        site=obj
                    ).value_from_key(
                        filter_group.group.key
                    )
                )
        return context_data

    class Meta:
        model = LocationSite
        fields = [
            'id',
            'name',
            'geometry',
            'location_type',
            'location_context',
            'refined_geomorphological',
            'owner'
        ]

    def get_site_detail_info(self, obj):
        site_coordinates = "{latitude}, {longitude}".format(
            latitude=round(obj.geometry_point.x, 3),
            longitude=round(obj.geometry_point.y, 3))

        def parse_string(string_in):
            return "Unknown" if not string_in else string_in

        try:
            river_name = parse_string(obj.river.name)
        except AttributeError:
            river_name = 'Unknown'
        site_detail_info = {
            'site_code': parse_string(obj.site_code),
            'site_coordinates': parse_string(site_coordinates),
            'site_description': parse_string(obj.site_description),
            'river': river_name
        }
        return site_detail_info

    def get_class_from_taxonomy(self, taxonomy):
        if taxonomy.rank != TaxonomicRank.CLASS.name:
            if taxonomy.parent:
                return self.get_class_from_taxonomy(taxonomy.parent)
        else:
            return taxonomy.canonical_name
        return None

    def get_site_climate_data(self, instance):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
                  'Sep', 'Oct', 'Nov', 'Dec']
        site_climate_data = dict()
        site_climate_data['temperature_chart'] = {}
        site_climate_data['temperature_chart']['values'] = []
        site_climate_data['temperature_chart']['keys'] = []
        site_climate_data['rainfall_chart'] = {}
        site_climate_data['rainfall_chart']['values'] = []
        site_climate_data['rainfall_chart']['keys'] = []

        location_contexts = LocationContext.objects.filter(site=instance)

        monthly_annual_temperature_values = location_contexts.filter(
            group__geocontext_group_key=
            'monthly_mean_daily_average_temperature_group'
        )

        monthly_annual_rainfall_values = location_contexts.filter(
            group__geocontext_group_key=
            'rainfall_group'
        )

        for month in months:
            temp_data = (
                monthly_annual_temperature_values.filter(
                    group__key__icontains=month)
            )
            if temp_data.exists():
                site_climate_data['temperature_chart']['values'].append(
                    round(float(temp_data[0].value))
                )
            else:
                site_climate_data['temperature_chart']['values'].append(0)
            site_climate_data['temperature_chart']['keys'].append(month)

            rain_data = (
                monthly_annual_rainfall_values.filter(
                    group__key__icontains=month)
            )
            if rain_data.exists():
                site_climate_data['rainfall_chart']['values'].append(
                    round(float(rain_data[0].value))
                )
            else:
                site_climate_data['rainfall_chart']['values'].append(0)
            site_climate_data['rainfall_chart']['keys'].append(month)

        site_climate_data['temperature_chart']['title'] = 'Annual Temperature'
        site_climate_data['rainfall_chart']['title'] = 'Annual Rainfall'
        return site_climate_data

    def to_representation(self, instance):
        result = super(
            LocationSiteDetailSerializer, self).to_representation(
            instance)
        records_occurrence = {}
        try:
            climate_data = self.get_site_climate_data(
                instance)
        except KeyError:
            climate_data = {}
        try:
            site_detail_info = self.get_site_detail_info(instance)
        except KeyError:
            site_detail_info = {}

        result['climate_data'] = climate_data
        result['records_occurrence'] = records_occurrence
        result['site_detail_info'] = site_detail_info

        return result
