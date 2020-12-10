from rest_framework import serializers
from bims.models import (
    BaseMapLayer
)


class BaseMapLayerSerializer(serializers.ModelSerializer):
    """
    Serializer for basemap layer model
    """
    class Meta:
        model = BaseMapLayer
        fields = '__all__'
