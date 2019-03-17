import json
from django.db.models import Count, F
from collections import defaultdict, Counter
from rest_framework import serializers
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.iucn_status import  IUCNStatus
from bims.serializers.location_site_serializer import LocationSiteSerializer
from bims.enums.taxonomic_rank import TaxonomicRank


class LocationSiteDetailSerializer(LocationSiteSerializer):
    """
    Serializer for location site detail.
    """
    geometry = serializers.SerializerMethodField()
    location_context_document_json = serializers.SerializerMethodField()

    def get_geometry(self, obj):
        geometry = obj.get_geometry()
        if geometry:
            return obj.get_geometry().json
        return ''

    def get_location_context_document_json(self, obj):
        if obj.location_context_document:
            return json.loads(obj.location_context_document)
        else:
            return ''

    class Meta:
        model = LocationSite
        fields = [
            'id',
            'name',
            'geometry',
            'location_type',
            'location_context_document_json',
        ]


    def get_site_detail_info(self, obj):
        site_coordinates = "{latitude}, {longitude}".format(
            latitude=round(obj.geometry_point.x, 3),
            longitude=round(obj.geometry_point.y, 3))
        try:
            context_data = json.loads(str(obj.location_context))
        except ValueError:
            context_data = {}
        try:
            geomorphological_zone = (context_data
                                     ['context_group_values']
                                     ['eco_geo_group']
                                     ['service_registry_values']
                                     ['geoclass']
                                     ['value'])
        except KeyError:
            geomorphological_zone = 'Unknown'
        def parse_string(string_in):
            return "Unknown" if not string_in else string_in
        site_detail_info = {
            'fbis_site_code': parse_string(obj.id),
            'site_coordinates': parse_string(site_coordinates),
            'site_description': parse_string(obj.site_description),
            'geomorphological_zone': parse_string(geomorphological_zone),
            'river': parse_string(obj.river.name)}
        return site_detail_info

    def get_class_from_taxonomy(self, taxonomy):
        if taxonomy.rank != TaxonomicRank.CLASS.name:
            if taxonomy.parent:
                return self.get_class_from_taxonomy(taxonomy.parent)
        else:
            return taxonomy.canonical_name
        return None

    def get_site_climate_data(self, context_document):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
                  'Sep', 'Oct', 'Nov', 'Dec']
        site_climate_data = {}
        site_climate_data['temperature_chart'] = {}
        site_climate_data['temperature_chart']['values'] = []
        site_climate_data['temperature_chart']['keys'] = []
        site_climate_data['rainfall_chart'] = {}
        site_climate_data['rainfall_chart']['values'] = []
        site_climate_data['rainfall_chart']['keys'] = []

        if context_document:
            context_document_dictionary = json.loads(context_document)
            monthly_annual_temperature_values = (
                context_document_dictionary
                ['context_group_values']
                ['monthly_mean_daily_average_temperature_group']
                ['service_registry_values'])
            monthly_annual_rainfall_values = (
                context_document_dictionary
                ['context_group_values']
                ['rainfall_group']
                ['service_registry_values'])
            count = 0
            for month_temperature in \
                    monthly_annual_temperature_values.iteritems():

                site_climate_data['temperature_chart']['values'].append(round(
                    month_temperature[1]['value'], 2))
                site_climate_data['temperature_chart']['keys'].append(
                    str(months[count]))
                count += 1
            count = 0

            for month_rainfall in monthly_annual_rainfall_values.iteritems():
                site_climate_data['rainfall_chart']['values'].append(round(
                    month_rainfall[1]['value'], 2))
                site_climate_data['rainfall_chart']['keys'].append(
                    str(months[count]))
                count += 1
        site_climate_data['temperature_chart']['title'] = 'Annual Temperature'
        site_climate_data['rainfall_chart']['title'] = 'Annual Rainfall'
        return site_climate_data

    def get_biodiversity_data(self, collection_results):
        biodiversity_data = defaultdict(dict)

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
        keys = origin_by_name_data.values_list('name', flat=True)
        values = origin_by_name_data.values_list('count', flat=True)
        biodiversity_data['fish']['origin_chart']['data'] = list(values)
        biodiversity_data['fish']['origin_chart']['keys'] = list(keys)
        cons_status_data = collection_results.annotate(
            name=F('taxonomy__iucn_status__category')
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )
        keys = cons_status_data.values_list('name', flat=True)
        values = cons_status_data.values_list('count', flat=True)
        biodiversity_data['fish']['cons_status_chart']['data'] = list(
            values)
        biodiversity_data['fish']['cons_status_chart']['keys'] = list(keys)
        endemism_status_data = collection_results.annotate(
            name=F('taxonomy__endemism__name')
        ).values(
            'name'
        ).annotate(
            count=Count('name')
        ).order_by(
            'name'
        )
        keys = endemism_status_data.values_list('name', flat=True)
        values = endemism_status_data.values_list('count', flat=True)
        biodiversity_data['fish']['endemism_chart']['data'] = list(values)
        biodiversity_data['fish']['endemism_chart']['keys'] = list(keys)

        biodiversity_data['occurrences'] = [0, 0, 0]
        biodiversity_data['occurrences'][0] = collection_results.count()

        biodiversity_data['number_of_taxa'] = [0, 0, 0]
        biodiversity_data['ecological_condition'] = ['TBA', 'TBA', 'TBA']
        return biodiversity_data


    def to_representation(self, instance):
        collection_ids = self.context.get("collection_ids")
        result = super(
            LocationSiteDetailSerializer, self).to_representation(
            instance)
        if collection_ids:
            collections = BiologicalCollectionRecord.objects.filter(
                id__in=collection_ids
            )
        else:
            collections = BiologicalCollectionRecord.objects.filter(
                site=instance,
                validated=True
            )
        records_occurrence = {}

        try:
            biodiversity_data = self.get_biodiversity_data(collections)
        except KeyError:
            biodiversity_data = {}
        try:
            climate_data = self.get_site_climate_data(
                instance.location_context)
        except KeyError:
            climate_data = {}
        try:
            site_detail_info = self.get_site_detail_info(instance)
        except KeyError:
            site_detail_info = {}

        result['iucn_name_list'] = IUCNStatus.CATEGORY_CHOICES
        result['origin_name_list'] = (
            BiologicalCollectionRecord.CATEGORY_CHOICES)
        result['climate_data'] = climate_data
        result['records_occurrence'] = records_occurrence
        result['biodiversity_data'] = biodiversity_data
        result['site_detail_info'] = site_detail_info

        return result

