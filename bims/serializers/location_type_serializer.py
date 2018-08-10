from rest_framework import serializers
from bims.models.location_type import LocationType


class LocationTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for location type model.
    """
    class Meta:
        model = LocationType
        fields = ['name', 'description']
