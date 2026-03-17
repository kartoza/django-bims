# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Serializers for Boundary models in API v1.
"""
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from bims.models.boundary import Boundary
from bims.models.user_boundary import UserBoundary


class BoundarySerializer(serializers.ModelSerializer):
    """
    Serializer for Boundary model (read-only system boundaries).
    """

    geometry = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = Boundary
        fields = [
            "id",
            "name",
            "code_name",
            "type",
            "geometry",
        ]
        read_only_fields = fields

    def get_geometry(self, obj):
        """Return geometry as GeoJSON."""
        if obj.geometry:
            return obj.geometry.json
        return None

    def get_type(self, obj):
        """Return boundary type name."""
        if obj.type:
            return obj.type.name
        return None


class BoundaryGeoSerializer(GeoFeatureModelSerializer):
    """
    GeoJSON serializer for boundaries.
    """

    class Meta:
        model = Boundary
        geo_field = "geometry"
        fields = ["id", "name", "code_name", "type"]


class UserBoundarySerializer(serializers.ModelSerializer):
    """
    Serializer for UserBoundary model (user-created boundaries).
    """

    geometry = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    created = serializers.DateTimeField(source="upload_date", read_only=True)

    class Meta:
        model = UserBoundary
        fields = [
            "id",
            "name",
            "geometry",
            "owner_name",
            "created",
        ]
        read_only_fields = ["id", "owner_name", "created"]

    def get_geometry(self, obj):
        """Return geometry as GeoJSON."""
        if obj.geometry:
            return obj.geometry.json
        return None

    def get_owner_name(self, obj):
        """Return owner's name."""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return None


class UserBoundaryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating user boundaries.
    """

    class Meta:
        model = UserBoundary
        fields = ["id", "name", "geometry"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Create boundary and set owner."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)
