from rest_framework import serializers
from bims.models.abundance_type import (
    AbundanceType
)


class AbundanceTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for Abundance Type model
    """
    specific_module = serializers.SerializerMethodField()

    def get_specific_module(self, obj: AbundanceType):
        if obj.specific_module:
            return obj.specific_module.name
        return ''

    class Meta:
        model = AbundanceType
        fields = [
            'name',
            'specific_module'
        ]
