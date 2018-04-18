from bims.models.location_site import LocationSite
from bims.serializers.location_site_serializer import LocationSiteSerializer
from bims.serializers.bio_collection_serializer import BioCollectionSerializer


class LocationSiteDetailSerializer(LocationSiteSerializer):
    """
    Serializer for location site detail.
    """
    biological_collection_record = BioCollectionSerializer(many=True)

    class Meta:
        model = LocationSite
        fields = [
            'id',
            'name',
            'geometry',
            'location_type',
            'biological_collection_record',
            ]
