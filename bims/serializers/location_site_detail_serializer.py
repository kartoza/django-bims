from django.db.models import Q
from django.utils.text import slugify
from rest_framework import serializers
from preferences import preferences
from bims.models.location_site import LocationSite
from bims.models.location_context import LocationContext
from bims.serializers.location_site_serializer import LocationSiteSerializer
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.location_context_filter_group_order import (
    LocationContextFilterGroupOrder
)
from bims.models.climate_data import ClimateData


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
                        key=filter_group.group.key,
                        layer_identifier=filter_group.group.layer_identifier
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

    def get_site_detail_info(self, obj: LocationSite):
        site_coordinates = "{latitude}, {longitude}".format(
            latitude=round(obj.geometry_point.x, 3),
            longitude=round(obj.geometry_point.y, 3))

        def parse_string(string_in):
            return "Unknown" if not string_in else string_in

        site_detail_info = {
            'site_code': parse_string(obj.site_code),
            'site_coordinates': parse_string(site_coordinates),
            'site_description': parse_string(obj.site_description),
            'ecosystem_type': obj.ecosystem_type if obj.ecosystem_type else 'Unspecified',
        }

        if preferences.SiteSetting.site_code_generator == 'fbis':
            try:
                if obj.legacy_river_name:
                    site_detail_info['river'] = parse_string(
                        obj.legacy_river_name)
                else:
                    site_detail_info['river'] = parse_string(obj.river.name)
            except AttributeError:
                site_detail_info['river'] = 'Unknown'

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
        months_number = [
            '01', '02', '03', '04', '05', '06',
            '07', '08', '09', '10', '11', '12'
        ]
        site_climate_data = dict()
        all_climate_data = ClimateData.objects.all()

        for climate_data in all_climate_data:
            key = slugify(climate_data.title)
            site_climate_data[key] = {}
            site_climate_data[key]['title'] = climate_data.title
            site_climate_data[key]['values'] = []
            site_climate_data[key]['keys'] = []

            geocontext_data = LocationContext.objects.filter(
                site=instance,
                group__geocontext_group_key=
                climate_data.climate_geocontext_group_key
            )

            month_index = 0
            for month in months:
                temp_data = (
                    geocontext_data.filter(
                        Q(group__key__icontains=month) |
                        Q(group__key__iendswith=months_number[month_index])
                    )
                )
                if temp_data.exists():
                    site_climate_data[key]['values'].append(
                        round(float(temp_data.first().value))
                    )
                else:
                    site_climate_data[key]['values'].append(0)
                site_climate_data[key]['keys'].append(month)
                month_index += 1

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
