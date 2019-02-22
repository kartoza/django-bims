import json
from collections import defaultdict, Counter
from rest_framework import serializers
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import BiologicalCollectionRecord
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
        context_data = json.loads(obj.location_context)
        geomorphological_zone = (context_data['context_group_values']
            ['eco_geo_group']
            ['service_registry_values']
            ['geoclass']
            ['value'])
        def parse_string(string_in):
            return "Unknown" if not string_in else string_in
        site_detail_info = {
            'fbis_site_code': parse_string(obj.id),
            'site_coordinates': parse_string(site_coordinates),
            'site_description': parse_string(obj.site_description),
            'geomorphological_zone': parse_string(geomorphological_zone),
            'river': parse_string(obj.river)}
        return site_detail_info

    def get_class_from_taxonomy(self, taxonomy):
        if taxonomy.rank != TaxonomicRank.CLASS.name:
            if taxonomy.parent:
                return self.get_class_from_taxonomy(taxonomy.parent)
        else:
            return taxonomy.canonical_name
        return None

    def get_site_climate_data(self, context_document):
        site_climate_data = {}
        site_climate_data['temperature_chart'] = {}
        site_climate_data['temperature_chart']['values'] = []
        site_climate_data['temperature_chart']['keys'] = []
        site_climate_data['rainfall_chart'] = {}
        site_climate_data['rainfall_chart']['values'] = []
        site_climate_data['rainfall_chart']['keys'] = []
        temperature_data = []
        rainfall_data = []

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
            temperature_total = 0
            rainfall_total = 0
            count = 0
            for month_temperature in \
                    monthly_annual_temperature_values.iteritems():
                count += 1
                site_climate_data['temperature_chart']['values'].append(
                    month_temperature[1]['value'])
                site_climate_data['temperature_chart']['keys'].append(
                    str(count))
            count = 0

            for month_rainfall in monthly_annual_rainfall_values.iteritems():
                count += 1
                site_climate_data['rainfall_chart']['values'].append(
                    month_rainfall[1]['value'])
                site_climate_data['rainfall_chart']['keys'].append(
                    str(count))

        site_climate_data['monthly_mean_daily_average_temperature_group']\
            ['title'] = 'Annual Temperature'
        site_climate_data['rainfall_chart']['title'] = 'Annual Rainfall'
        return site_climate_data


    def get_biodiversity_data(self, instance):
        biodiversity_data = defaultdict(dict)
        collection_ids = self.context.get("collection_ids")
        if collection_ids:
            collections = BiologicalCollectionRecord.objects.filter(
                id__in=collection_ids
            )
        else:
            collections = BiologicalCollectionRecord.objects.filter(
                site=instance,
                validated=True
            )
        taxa = self.get_origin_cons_endemsim_data(collections)
        # If I found more than one class of animal
        if 'Actinopterygii' not in taxa:
            print('Hey there, you are not a fish!')
        else:
            biodiversity_data['fish'] = {}
            biodiversity_data['fish']['origin_chart'] = {}
            biodiversity_data['fish']['cons_status_chart'] = {}
            biodiversity_data['fish']['endemism_chart'] = {}
            biodiversity_data['fish']['origin_chart']['data'] = (
                taxa['Actinopterygii']['origin_chart']['data'])
            biodiversity_data['fish']['origin_chart']['keys'] = (
                taxa['Actinopterygii']['origin_chart']['keys'])
            biodiversity_data['fish']['cons_status_chart']['data'] = (
                taxa['Actinopterygii']['cons_status_chart']['data'])
            biodiversity_data['fish']['cons_status_chart']['keys'] = (
                taxa['Actinopterygii']['cons_status_chart']['keys'])
            biodiversity_data['fish']['endemism_chart']['data'] = (
                taxa['Actinopterygii']['endemism_chart']['data'])
            biodiversity_data['fish']['endemism_chart']['keys'] = (
                taxa['Actinopterygii']['endemism_chart']['keys'])
        biodiversity_data['taxa'] = taxa

        biodiversity_data['occurrences'] = [0, 0, 0]
        biodiversity_data['occurrences'][0] = (
            sum(taxa['Actinopterygii']['occurrences']))

        biodiversity_data['number_of_taxa'] = [0, 0 ,0]
        biodiversity_data['number_of_taxa'][0] = (
            len(taxa['Actinopterygii']['number_of_taxa']))
        biodiversity_data['ecological_condition'] = ['TBA', 'TBA', 'TBA']
        return biodiversity_data

    def get_origin_cons_endemsim_data(self, collections):
        taxa = defaultdict(dict)

        for model in collections:
            if not (model.taxonomy.class_name in taxa):
                taxa[model.taxonomy.class_name]['origin_data'] = []
                taxa[model.taxonomy.class_name]['cons_status_data'] = []
                taxa[model.taxonomy.class_name]['endemism_data'] = []
                taxa[model.taxonomy.class_name]['occurrence_data'] = []

            taxa[model.taxonomy.class_name]['origin_data'].append(
                model.category)
            taxa[model.taxonomy.class_name]['cons_status_data'].append(
                model.taxonomy.iucn_status.category)
            taxa[model.taxonomy.class_name]['endemism_data'].append(
                model.taxonomy.endemism)
            taxa[model.taxonomy.class_name]['occurrence_data'].append(
                model.taxonomy.scientific_name)

        for class_name in taxa:
            if 'origin_chart' not in taxa[class_name]:
                taxa[class_name]['origin_chart'] = {}
                taxa[class_name]['origin_chart']['data'] = []
                taxa[class_name]['origin_chart']['keys'] = []
                taxa[class_name]['cons_status_chart'] = {}
                taxa[class_name]['cons_status_chart']['data'] = []
                taxa[class_name]['cons_status_chart']['keys'] = []
                taxa[class_name]['endemism_chart'] = {}
                taxa[class_name]['endemism_chart']['data'] = []
                taxa[class_name]['endemism_chart']['keys'] = []
                taxa[class_name]['occurrences'] = []
                taxa[class_name]['number_of_taxa'] = []

            data_counter_origin = (
                Counter(taxa[class_name]['origin_data']))
            data_counter_cons_status = (
                Counter(taxa[class_name]['cons_status_data']))
            data_counter_endemism = (
                Counter(taxa[class_name]['endemism_data']))
            data_counter_occurrence = (
                Counter(taxa[class_name]['occurrence_data']))

            taxa[class_name]['origin_chart']['data'].append(
                data_counter_origin.values()[0])
            taxa[class_name]['origin_chart']['keys'].append(
                data_counter_origin.keys()[0])

            taxa[class_name]['cons_status_chart']['data'].append(
                data_counter_cons_status.values())
            taxa[class_name]['cons_status_chart']['data'] = (
                taxa[class_name]['cons_status_chart']['data'][0])
            taxa[class_name]['cons_status_chart']['keys'].append(
                data_counter_cons_status.keys())
            taxa[class_name]['cons_status_chart']['keys'] = (
                taxa[class_name]['cons_status_chart']['keys'][0])

            taxa[class_name]['endemism_chart']['data'].append(
                data_counter_endemism.values()[0])
            taxa[class_name]['endemism_chart']['keys'].append(
                data_counter_endemism.keys()[0])
            taxa[class_name]['occurrences'].append(
                data_counter_occurrence.values()[0])
            taxa[class_name]['number_of_taxa'].append(
                data_counter_occurrence.keys()[0])
        return taxa

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
        module_info = {}
        site_detail_info = self.get_site_detail_info(instance)
        for model in collections:
            taxonomy = model.taxonomy
            category = model.category
            year_collected = model.collection_date.year
            if taxonomy:
                taxon_id = taxonomy.gbif_key
                taxon_class = self.get_class_from_taxonomy(taxonomy)
                if not taxon_class:
                    taxon_class = 'No Class'

                try:
                    records_occurrence[taxon_class]
                except KeyError:
                    records_occurrence[taxon_class] = {}

                species_list = records_occurrence[taxon_class]
                try:
                    species_list[taxonomy.canonical_name]
                except KeyError:
                    species_list[taxonomy.canonical_name] = {
                        'taxon_id': taxonomy.id,
                        'taxonomy': taxon_id,
                        'category': category,
                        'count': 0,
                        'data_by_year': {}
                    }
                species_list[taxonomy.canonical_name]['count'] += 1

                if year_collected not in \
                        species_list[taxonomy.canonical_name][
                            'data_by_year']:
                    species_list[taxonomy.canonical_name]['data_by_year'][
                        year_collected] = 1
                else:
                    species_list[taxonomy.canonical_name]['data_by_year'][
                        year_collected] += 1

            # get per module info
            module = model.get_children()
            try:
                module = module._meta.verbose_name
            except AttributeError:
                module = 'base'

            try:
                module_info[module]
            except KeyError:
                module_info[module] = {
                    'count': 0,
                    'categories': {},
                    'iucn_status': {
                        'sensitive': 0,
                        'non-sensitive': 0
                    }
                }
            module_info[module]['count'] += 1

            # get per category info
            if model.category:
                category = model.category
                try:
                    module_info[module]['categories'][category]
                except KeyError:
                    module_info[module]['categories'][category] = 0
                module_info[module]['categories'][category] += 1

            # get per iucn_status info
            if model.taxonomy and model.taxonomy.iucn_status:
                sensitive = model.taxonomy.iucn_status.sensitive
                if sensitive:
                    module_info[module]['iucn_status']['sensitive'] += 1
                else:
                    module_info[module]['iucn_status']['non-sensitive'] += 1

        biodiversity_data = self.get_biodiversity_data(instance)
        climate_data = self.get_site_climate_data(instance.location_context)

        result['climate_data'] = climate_data
        result['records_occurrence'] = records_occurrence
        result['modules_info'] = module_info
        result['biodiversity_data'] = biodiversity_data
        result['site_detail_info'] = site_detail_info

        return result
