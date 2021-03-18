# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '07/06/18'

from bims.models.biological_collection_record import BiologicalCollectionRecord
from rest_framework import serializers


class BiologicalCollectionRecordDocSerializer(serializers.ModelSerializer):
    geometry = serializers.SerializerMethodField()
    record_type = serializers.SerializerMethodField()
    taxon_gbif_id = serializers.SerializerMethodField()

    def get_record_type(self, obj):
        return 'bio'

    def get_geometry(self, object):
        return object.site.get_geometry().geojson

    def get_taxon_gbif_id(self, object):
        if object.taxonomy:
            return object.taxonomy.id
        else:
            return None

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            'id',
            'original_species_name',
            'collector',
            'collection_date',
            'geometry',
            'taxon_gbif_id',
            'record_type'
        ]
