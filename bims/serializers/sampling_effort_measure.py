from rest_framework import serializers
from bims.models.sampling_effort_measure import (
    SamplingEffortMeasure
)


class SamplingEffortMeasureSerializer(serializers.ModelSerializer):
    """
    Serializer for Sampling Effort Measure model
    """
    specific_module = serializers.SerializerMethodField()

    def get_specific_module(self, obj: SamplingEffortMeasure):
        if obj.specific_module:
            return obj.specific_module.name
        return ''

    class Meta:
        model = SamplingEffortMeasure
        fields = [
            'name',
            'specific_module'
        ]
