from rest_framework import serializers
from bims.models import (
    Survey, ChemicalRecord, SurveyDataOption, SurveyData, SurveyDataValue
)


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


class SurveyDataOptionSerializer(serializers.ModelSerializer):
    """
    Serializer for survey data option model.
    """
    selected = serializers.SerializerMethodField()

    class Meta:
        model = SurveyDataOption
        fields = [
            'pk',
            'option',
            'selected'
        ]

    def get_selected(self, instance):
        survey_id = self.context.get('survey_id')
        return SurveyDataValue.objects.filter(
            survey_data=instance.survey_data,
            survey_data_option=instance,
            survey__id=survey_id
        ).exists()


class SurveyDataSerializer(serializers.ModelSerializer):
    """
    Serializer for super data model.
    """
    option_set = serializers.SerializerMethodField()

    class Meta:
        model = SurveyData
        fields = [
            'pk',
            'name',
            'option_set'
        ]

    def get_option_set(self, instance):
        options = instance.surveydataoption_set.all().order_by(
            'display_order')
        return SurveyDataOptionSerializer(
            options,
            many=True,
            context={'survey_id': self.context.get('survey_id')}).data
