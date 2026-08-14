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


class ChemicalRecordsOneRowSerializer(serializers.ModelSerializer):
    date_record = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    chemical_code = serializers.SerializerMethodField()
    source_references = serializers.SerializerMethodField()
    location_site = serializers.SerializerMethodField()

    class Meta:
        model = ChemicalRecord
        fields = [
            'id',
            'date_record',
            'name',
            'chemical_code',
            'unit',
            'value',
            'location_site',
            'source_references'
        ]

    def get_date_record(self, obj):
        return str(obj.date)

    def get_unit(self, obj):
        return obj.chem.chem_unit.unit

    def get_name(self, obj):
        return obj.chem.chem_description

    def get_chemical_code(self, obj):
        return obj.chem.chem_code

    def get_source_references(self, obj):
        label = None
        if obj.source_reference:
            label = (
                obj.source_reference.get_source_unicode()
                or str(obj.source_reference)
            )
        if not label and obj.survey_id:
            bio_source_by_survey = self.context.get('bio_source_by_survey')
            if bio_source_by_survey is not None:
                label = bio_source_by_survey.get(obj.survey_id)
            else:
                from bims.models.biological_collection_record import (
                    BiologicalCollectionRecord
                )
                bio = BiologicalCollectionRecord.objects.filter(
                    survey_id=obj.survey_id
                ).exclude(
                    source_reference__isnull=True
                ).select_related('source_reference').first()
                if bio:
                    label = (
                        bio.source_reference.get_source_unicode()
                        or str(bio.source_reference)
                    )
        return label or '-'

    def get_location_site(self, obj):
        if obj.location_site:
            return obj.location_site.location_site_identifier
        elif obj.survey:
            return obj.survey.site.location_site_identifier
        return '-'
