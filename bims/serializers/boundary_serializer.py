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
