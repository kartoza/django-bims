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


class BoundaryGeojsonSerializer(GeoFeatureModelSerializer):
    geometry = GeometrySerializerMethodField()

    class Meta:
        model = Boundary
        geo_field = 'geometry'
        fields = []

    def get_geometry(self, obj):
        return obj.geometry
