import json
from django.db.models import Count, F, Q
from collections import defaultdict
from rest_framework import serializers
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.iucn_status import IUCNStatus
from bims.serializers.location_site_serializer import LocationSiteSerializer
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.taxon_group import TaxonGroup
from bims.models.taxonomy import Taxonomy


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
        if obj.location_context:
            return json.loads(obj.location_context)
        else:
            return {}

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

        def parse_string(string_in):
            return "Unknown" if not string_in else string_in

        try:
            river_name = parse_string(obj.river.name)
        except AttributeError:
            river_name = 'Unknown'
        site_detail_info = {
            'fbis_site_code': parse_string(obj.site_code),
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

        fish_collections = BiologicalCollectionRecord.objects.none()
        fish_group = TaxonGroup.objects.filter(
            name__icontains='fish'
        )
        if fish_group.exists():
            taxon_groups = fish_group.values_list(
                'taxonomies', flat=True
            ).distinct('taxonomies')
            taxa = Taxonomy.objects.filter(pk__in=taxon_groups)
            modules_query = Q()
            for taxon in taxa:
                children = taxon.get_all_children()
                children = children.filter(
                    biologicalcollectionrecord__isnull=False
                ).distinct()
                if children:
                    modules_query = Q(
                        **{'taxonomy__in': children}
                    )
            fish_collections = collection_results.filter(modules_query)

        biodiversity_data['fish'] = {}
        biodiversity_data['fish']['origin_chart'] = {}
        biodiversity_data['fish']['cons_status_chart'] = {}
        biodiversity_data['fish']['endemism_chart'] = {}
        origin_by_name_data = fish_collections.annotate(
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
        cons_status_data = fish_collections.annotate(
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
        endemism_status_data = fish_collections.annotate(
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
        biodiversity_data['occurrences'][0] = fish_collections.count()

        biodiversity_data['number_of_taxa'] = [
            fish_collections.distinct('taxonomy').count(),
            0,
            0,
        ]

        biodiversity_data['ecological_condition'] = ['TBA', 'TBA', 'TBA']
        return biodiversity_data

    def to_representation(self, instance):
        collection_results = self.context.get("collection_results")
        result = super(
            LocationSiteDetailSerializer, self).to_representation(
            instance)
        if collection_results:
            collections = collection_results
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
