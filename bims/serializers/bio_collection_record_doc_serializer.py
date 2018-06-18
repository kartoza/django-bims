# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '07/06/18'


from bims.models.biological_collection_record import BiologicalCollectionRecord
from rest_framework import serializers


class BiologicalCollectionRecordDocSerializer(serializers.ModelSerializer):

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            'original_species_name',
            'collector',
            'category',
            'collection_date'
        ]
