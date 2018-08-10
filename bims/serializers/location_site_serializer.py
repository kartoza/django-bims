from rest_framework import serializers
from bims.models.location_site import LocationSite
from bims.serializers.location_type_serializer import LocationTypeSerializer


class LocationSiteSerializer(serializers.ModelSerializer):
    """
    Serializer for location site model.
    """
    geometry = serializers.SerializerMethodField()
    location_type = LocationTypeSerializer(read_only=True)
    record_type = serializers.SerializerMethodField()

    def get_record_type(self, obj):
        return 'site'

    def get_geometry(self, obj):
        geometry = obj.get_geometry()
        if geometry:
            return obj.get_geometry().json
        return ''

    class Meta:
        model = LocationSite
        fields = ['id', 'name', 'geometry', 'location_type', 'record_type']


class LocationSiteClusterSerializer(serializers.ModelSerializer):
    """
    Serializer for location site model for cluster.
    """
    location_type = LocationTypeSerializer(read_only=True)
    record_type = serializers.SerializerMethodField()

    def get_record_type(self, obj):
        return 'site'

    class Meta:
        model = LocationSite
        fields = ['id', 'name', 'location_type', 'record_type']


class LocationOccurrencesSerializer(serializers.ModelSerializer):
    """
    Serializer for location site model for cluster.
    """
    count = serializers.SerializerMethodField()
    record_type = serializers.SerializerMethodField()
    geometry = serializers.SerializerMethodField()

    def get_count(self, obj):
        if hasattr(obj, 'num_occurrences'):
            return obj.num_occurrences
        else:
            return 0

    def get_record_type(self, obj):
        return 'site'

    def get_geometry(self, obj):
        geometry = obj.get_geometry()
        if geometry:
            return obj.get_geometry().json
        return ''

    class Meta:
        model = LocationSite
        fields = ['id', 'name', 'count', 'record_type', 'geometry']
