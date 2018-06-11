# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '07/06/18'


from bims.models.biological_collection_record import BiologicalCollectionRecord
from rest_framework import serializers


class BiologicalCollectionRecordDocSerializer(serializers.ModelSerializer):
    collection_date = serializers.SerializerMethodField()

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            'original_species_name',
            'collection_date',
            'collector',
        ]

    def get_collection_date(self, obj):
        return obj.collection_date
