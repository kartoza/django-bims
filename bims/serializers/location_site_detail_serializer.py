import json
from rest_framework import serializers
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.location_site_serializer import LocationSiteSerializer


class LocationSiteDetailSerializer(LocationSiteSerializer):
    """
    Serializer for location site detail.
    """
    records_occurrence = serializers.SerializerMethodField()
    geometry = serializers.SerializerMethodField()
    location_context_document_json = serializers.SerializerMethodField()

    def get_records_occurrence(self, obj):
        collections = BiologicalCollectionRecord.objects.filter(
            site=obj,
            validated=True
        )
        records = {}
        for model in collections:
            taxon_gbif_id = model.taxon_gbif_id
            if taxon_gbif_id:
                taxon_id = taxon_gbif_id.id
                taxon_class = taxon_gbif_id.taxon_class
                try:
                    records[taxon_class]
                except KeyError:
                    records[taxon_class] = {}

                species_list = records[taxon_class]
                try:
                    species_list[taxon_gbif_id.common_name]
                except KeyError:
                    species_list[taxon_gbif_id.common_name] = {
                        'taxon_gbif_id': taxon_id,
                        'count': 0
                    }
                species_list[taxon_gbif_id.common_name]['count'] += 1

        return records

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
            'records_occurrence',
            'location_context_document_json',
        ]
