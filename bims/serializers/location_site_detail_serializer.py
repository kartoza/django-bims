import json
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

    def get_class_from_taxonomy(self, taxonomy):
        if taxonomy.rank != TaxonomicRank.CLASS.name:
            if taxonomy.parent:
                return self.get_class_from_taxonomy(taxonomy.parent)
        else:
            return taxonomy.canonical_name
        return None

    def get_site_details(self):
        # get single site detailed dashboard overview data

        overview = {}
        overview['title'] = []
        overview['value'] = []
        catchments = {}
        catchments['title'] = []
        catchments['value'] = []
        sa_ecoregions = {}
        sa_ecoregions['title'] = []
        sa_ecoregions['value'] = []
        sub_water_management_areas = {}
        sub_water_management_areas['title'] = []
        sub_water_management_areas['value'] = []

        overview['title'].append('FBIS Site Code')
        overview['value'].append('value')

        overview['title'].append('Site coordinates')
        overview['value'].append('')

        overview['title'].append('Site description')
        overview['value'].append('value')

        overview['title'].append('River')
        overview['value'].append('value')

        overview['title'].append('Geomorphological zone')
        overview['value'].append('value')

        overview['title'].append('River Management Units')
        overview['value'].append('value')

        catchments['title'].append('Primary')
        catchments['value'].append('value')

        catchments['title'].append('Secondary')
        catchments['value'].append('value')

        catchments['title'].append('Tertiary')
        catchments['value'].append('value')

        catchments['title'].append('Quaternary')
        catchments['value'].append('value')

        catchments['title'].append('Quinary')
        catchments['value'].append('value')

        sub_water_management_areas['title'].append(
            'Sub-Water Management Areas')
        sub_water_management_areas['value'].append('value')

        sub_water_management_areas['title'].append(
            'Water Management Areas (WMA)')
        sub_water_management_areas['value'].append('value')

        sa_ecoregions['title'].append('Ecoregion Level 1')
        sa_ecoregions['value'].append('value')

        sa_ecoregions['title'].append('Ecoregion Level 2')
        sa_ecoregions['value'].append('value')

        sa_ecoregions['title'].append('Freshwater Ecoregion')
        sa_ecoregions['value'].append('value')

        sa_ecoregions['title'].append('Province')
        sa_ecoregions['value'].append('value')

        result = {}
        result['overview'] = overview
        result['catchments'] = catchments
        result['sub_water_management_areas'] = sub_water_management_areas
        result['sa_ecoregions'] = sa_ecoregions

        return result

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


        result['records_occurrence'] = records_occurrence
        result['modules_info'] = module_info
        result['site_details'] = self.get_site_details()

        return result
