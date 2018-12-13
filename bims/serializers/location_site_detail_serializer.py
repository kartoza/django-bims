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

    def get_geometry(self, obj):
        geometry = obj.get_geometry()
        if geometry:
            return obj.get_geometry().json
        return ''

    class Meta:
        model = LocationSite
        fields = [
            'id',
            'name',
            'geometry',
            'location_type'
        ]

    def get_class_from_taxonomy(self, taxonomy):
        if taxonomy.rank != TaxonomicRank.CLASS.name:
            if taxonomy.parent:
                return self.get_class_from_taxonomy(taxonomy.parent)
        else:
            return taxonomy.canonical_name
        return None

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
        return result
