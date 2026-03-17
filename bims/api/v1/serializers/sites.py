# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Serializers for LocationSite model in API v1.
"""
from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from bims.models.location_site import LocationSite
from bims.models.location_type import LocationType
from bims.models.location_context import LocationContext
from bims.models.location_context_filter_group_order import LocationContextFilterGroupOrder


class LocationTypeSerializer(serializers.ModelSerializer):
    """Serializer for LocationType."""

    class Meta:
        model = LocationType
        fields = ["id", "name", "description", "allowed_geometry"]


class LocationSiteListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing location sites.

    Provides essential fields for list views with geometry as GeoJSON.
    """

    geometry = serializers.SerializerMethodField()
    location_type = LocationTypeSerializer(read_only=True)
    river_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = LocationSite
        fields = [
            "id",
            "name",
            "site_code",
            "site_description",
            "geometry",
            "location_type",
            "river_name",
            "ecosystem_type",
            "wetland_name",
            "owner_name",
            "validated",
            "created",
            "modified",
        ]
        read_only_fields = fields

    def get_geometry(self, obj):
        """Return geometry as GeoJSON."""
        geometry = obj.get_geometry()
        if geometry:
            return geometry.json
        return None

    def get_river_name(self, obj):
        """Return river name if available."""
        if obj.legacy_river_name:
            return obj.legacy_river_name
        return obj.river.name if obj.river else None

    def get_owner_name(self, obj):
        """Return owner's full name."""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip() or obj.owner.username
        return None


class LocationSiteDetailSerializer(LocationSiteListSerializer):
    """
    Detailed serializer for single location site view.

    Includes location context and additional data.
    """

    location_context = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    climate_data = serializers.SerializerMethodField()

    class Meta:
        model = LocationSite
        fields = LocationSiteListSerializer.Meta.fields + [
            "location_context",
            "coordinates",
            "climate_data",
            "refined_geomorphological",
            "original_geomorphological",
            "land_owner_detail",
            "map_reference",
            "additional_data",
            "legacy_site_code",
            "legacy_river_name",
        ]
        read_only_fields = fields

    def get_location_context(self, obj):
        """Return location context data organized by filter groups."""
        context_data = {}
        filter_groups = LocationContextFilterGroupOrder.objects.filter(
            show_in_side_panel=True
        ).order_by("group_display_order")

        for filter_group in filter_groups:
            if filter_group.group.name not in context_data:
                context_data[filter_group.group.name] = LocationContext.objects.filter(
                    site=obj
                ).value_from_key(
                    key=filter_group.group.key,
                    layer_identifier=filter_group.group.layer_identifier,
                )
        return context_data

    def get_coordinates(self, obj):
        """Return coordinates as lat/lon."""
        if obj.geometry_point:
            return {
                "latitude": round(obj.geometry_point.y, 6),
                "longitude": round(obj.geometry_point.x, 6),
            }
        return None

    def get_climate_data(self, obj):
        """Return climate data if available."""
        # This can be extended to fetch climate data from LocationContext
        return None


class LocationSiteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating location sites.
    """

    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    location_type_id = serializers.PrimaryKeyRelatedField(
        queryset=LocationType.objects.all(),
        source="location_type",
        write_only=True,
    )

    class Meta:
        model = LocationSite
        fields = [
            "id",
            "name",
            "site_code",
            "site_description",
            "location_type_id",
            "latitude",
            "longitude",
            "ecosystem_type",
            "wetland_name",
            "refined_geomorphological",
            "land_owner_detail",
            "map_reference",
            "additional_data",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Validate coordinates if provided."""
        latitude = attrs.pop("latitude", None)
        longitude = attrs.pop("longitude", None)

        if latitude is not None and longitude is not None:
            if not (-90 <= latitude <= 90):
                raise serializers.ValidationError({"latitude": "Latitude must be between -90 and 90."})
            if not (-180 <= longitude <= 180):
                raise serializers.ValidationError({"longitude": "Longitude must be between -180 and 180."})
            attrs["geometry_point"] = Point(longitude, latitude)

        return attrs

    def create(self, validated_data):
        """Create location site and set owner."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["owner"] = request.user
        return super().create(validated_data)


class LocationSiteSummarySerializer(serializers.Serializer):
    """
    Serializer for location site summary statistics.
    """

    total_sites = serializers.IntegerField()
    validated_sites = serializers.IntegerField()
    pending_sites = serializers.IntegerField()
    sites_with_records = serializers.IntegerField()
    ecosystem_type_counts = serializers.DictField()


class LocationSiteGeoSerializer(GeoFeatureModelSerializer):
    """
    GeoJSON serializer for location sites.

    Returns sites as GeoJSON FeatureCollection.
    """

    river_name = serializers.SerializerMethodField()

    class Meta:
        model = LocationSite
        geo_field = "geometry_point"
        fields = [
            "id",
            "name",
            "site_code",
            "river_name",
            "ecosystem_type",
        ]

    def get_river_name(self, obj):
        """Return river name if available."""
        if obj.legacy_river_name:
            return obj.legacy_river_name
        return obj.river.name if obj.river else None
