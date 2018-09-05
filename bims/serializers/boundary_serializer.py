import json
from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer, GeometrySerializerMethodField)
from bims.models import Boundary
from bims.models.cluster import Cluster


class BoundarySerializer(serializers.ModelSerializer):
    """
    Serializer for boundary model.
    """
    count = serializers.SerializerMethodField()
    boundary_type = serializers.SerializerMethodField()
    point = serializers.SerializerMethodField()

    def get_count(self, obj):
        try:
            cluster = Cluster.objects.get(
                boundary=obj,
                module='location site'
            )
            return cluster.site_count
        except Cluster.DoesNotExist:
            return 0

    def get_point(self, obj):
        if obj.centroid:
            center = obj.centroid.centroid
        else:
            center = obj.geometry.centroid
        return [center.x, center.y]

    def get_boundary_type(self, obj):
        return obj.type.name

    class Meta:
        model = Boundary
        exclude = ['geometry']


class BoundaryClusterSerializer(serializers.ModelSerializer):
    """
    Serializer for boundary model for cluster returns.
    """
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    geometry = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.boundary.id

    def get_type(self, obj):
        return 'Feature'

    def get_geometry(self, obj):
        if obj.boundary.centroid:
            center = obj.boundary.centroid.centroid
        else:
            center = obj.boundary.geometry.centroid
        coordinates = [center.x, center.y]
        return {
            "type": "Point",
            "coordinates": coordinates
        }

    def get_properties(self, obj):
        if obj.site_count == 1:
            details = json.loads(obj.details)
            try:
                return details['site_detail']
            except KeyError:
                pass
        return {'count': obj.site_count}

    class Meta:
        model = Cluster
        exclude = ['details', 'boundary', 'site_count', 'module']


class BoundaryGeojsonSerializer(GeoFeatureModelSerializer):
    geometry = GeometrySerializerMethodField()

    class Meta:
        model = Boundary
        geo_field = 'geometry'
        fields = []

    def get_geometry(self, obj):
        return obj.geometry
