# coding=utf-8
from rest_framework import serializers
from bims.models.chemical_record import ChemicalRecord


class ChemicalRecordsSerializer(serializers.ModelSerializer):
    str_date = serializers.SerializerMethodField()

    class Meta:
        model = ChemicalRecord
        fields = ['value', 'str_date']

    def get_str_date(self, obj):
        return str(obj.date)
