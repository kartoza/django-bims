from bims.models.location_site import LocationSite
from bims.serializers.location_site_serializer import LocationSiteSerializer


class LocationSiteDetailSerializer(LocationSiteSerializer):
    """
    Serializer for location site detail.
    """

    class Meta:
        model = LocationSite
        fields = [
            'id',
            'name',
            'geometry',
            'location_type',
            'fish_collection_records']
