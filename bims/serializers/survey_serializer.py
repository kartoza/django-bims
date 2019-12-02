from rest_framework import serializers
from bims.models import Survey, ChemicalRecord


class SurveySerializer(serializers.ModelSerializer):
    """
    Serializer for survey model.
    """
    chemical_record_count = serializers.SerializerMethodField()

    def get_chemical_record_count(self, obj):
        return ChemicalRecord.objects.filter(
            survey=obj).count()

    class Meta:
        model = Survey
        fields = '__all__'
