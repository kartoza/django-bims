from rest_framework import serializers
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.location_type_serializer import LocationTypeSerializer


class LocationSiteSerializer(serializers.ModelSerializer):
    """
    Serializer for location site model.
    """
    geometry = serializers.SerializerMethodField()
    location_type = LocationTypeSerializer(read_only=True)
    record_type = serializers.SerializerMethodField()
    river_name = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    user_site_code = serializers.CharField(source='legacy_site_code', read_only=True)
    user_river_name = serializers.CharField(source='legacy_river_name', read_only=True)

    def get_description(self, obj):
        return obj.site_description

    def get_owner(self, obj):
        return (
            f'{obj.owner.first_name} {obj.owner.last_name}'
            if obj.owner else ''
        )

    def get_river_name(self, obj):
        return obj.river.name if obj.river else ''

    def get_record_type(self, obj):
        return 'site'

    def get_geometry(self, obj):
        geometry = obj.get_geometry()
        if geometry:
            return obj.get_geometry().json
        return ''

    class Meta:
        model = LocationSite
        fields = [
            'id', 'site_code',
            'name', 'geometry',
            'location_type',
            'record_type',
            'river_name',
            'user_site_code',
            'user_river_name',
            'owner',
            'description',
            'ecosystem_type',
            'wetland_name',
            'user_wetland_name'
        ]


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


class LocationSitesCoordinateSerializer(serializers.ModelSerializer):
    """
    Serializer for location site model for site detail.
    """
    id = serializers.SerializerMethodField()
    coord = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.location_site_id

    def get_name(self, obj):
        return obj.location_site_name

    def get_coord(self, obj):
        return obj.location_coordinates

    class Meta:
        model = BiologicalCollectionRecord
        fields = ['id', 'coord', 'name']


class LocationOccurrencesSerializer(serializers.ModelSerializer):
    """
    Serializer for location site model for cluster.
    """
    count = serializers.SerializerMethodField()
    record_type = serializers.SerializerMethodField()
    geometry = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.name

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
