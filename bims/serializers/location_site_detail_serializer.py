import json
from rest_framework import serializers
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.location_site_serializer import LocationSiteSerializer


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
            taxon_gbif_id = model.taxon_gbif_id
            category = model.category
            if taxon_gbif_id:
                taxon_id = taxon_gbif_id.gbif_id
                taxon_class = taxon_gbif_id.taxon_class
                try:
                    records_occurrence[taxon_class]
                except KeyError:
                    records_occurrence[taxon_class] = {}

                species_list = records_occurrence[taxon_class]
                try:
                    species_list[taxon_gbif_id.common_name]
                except KeyError:
                    species_list[taxon_gbif_id.common_name] = {
                        'taxon_id': taxon_gbif_id.id,
                        'taxon_gbif_id': taxon_id,
                        'category': category,
                        'count': 0
                    }
                species_list[taxon_gbif_id.common_name]['count'] += 1

            # get per module info
            module = model.get_children()
            if not module:
                module = 'base'
            else:
                module = module._meta.verbose_name

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
            if model.taxon_gbif_id and model.taxon_gbif_id.iucn_status:
                sensitive = model.taxon_gbif_id.iucn_status.sensitive
                if sensitive:
                    module_info[module]['iucn_status']['sensitive'] += 1
                else:
                    module_info[module]['iucn_status']['non-sensitive'] += 1

        result['records_occurrence'] = records_occurrence
        result['modules_info'] = module_info
        return result
