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
    count = serializers.SerializerMethodField()
    site_id = serializers.SerializerMethodField()

    def get_site_id(self, obj):
        return obj.id

    def get_count(self, obj):
        if hasattr(obj, 'num_occurences'):
            return obj.num_occurences
        else:
            return 0

    def get_record_type(self, obj):
        if 'record_type' in self.context:
            return self.context['record_type']
        return 'site'

    class Meta:
        model = LocationSite
        fields = ['id', 'name', 'location_type', 'record_type',
                  'site_id', 'count']
