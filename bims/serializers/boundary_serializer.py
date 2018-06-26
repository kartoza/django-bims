from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer, GeometrySerializerMethodField
)
from rest_framework import serializers
from bims.models import Boundary
from bims.models.cluster import Cluster
from bims.serializers.cluster_serializer import ClusterSerializer


class BoundarySerializer(serializers.ModelSerializer):
    """
    Serializer for boundary model.
    """
    cluster_data = serializers.SerializerMethodField()
    boundary_type = serializers.SerializerMethodField()
    point = serializers.SerializerMethodField()

    def get_cluster_data(self, obj):
        data = {}
        clusters = Cluster.objects.filter(boundary=obj)
        for cluster in clusters:
            data[cluster.module] = ClusterSerializer(cluster).data
        return data

    def get_point(self, obj):
        center = obj.geometry.centroid
        return [center.x, center.y]

    def get_boundary_type(self, obj):
        return obj.type.name

    class Meta:
        model = Boundary
        exclude = ['geometry']


class BoundaryGeoSerializer(GeoFeatureModelSerializer):
    """
    Serializer for boundary model in geojson.
    """
    geometry = GeometrySerializerMethodField()

    def get_geometry(self, obj):
        return obj.geometry

    class Meta:
        model = Boundary
        geo_field = 'geometry'
        exclude = ['type']

    def to_representation(self, instance):
        result = super(
            BoundaryGeoSerializer, self).to_representation(
            instance)
        return result
