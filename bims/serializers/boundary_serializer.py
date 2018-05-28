from rest_framework import serializers
from bims.models import Boundary
from bims.models.cluster import Cluster


class BoundarySerializer(serializers.ModelSerializer):
    """
    Serializer for boundary model.
    """
    cluster_data = serializers.SerializerMethodField()
    point = serializers.SerializerMethodField()

    def get_cluster_data(self, obj):
        data = {}
        clusters = Cluster.objects.filter(boundary=obj)
        for cluster in clusters:
            data[cluster.module] = {
                'site_count': cluster.site_count,
                'survey_count': cluster.survey_count,
                'record_count': cluster.record_count
            }
        return data

    def get_point(self, obj):
        center = obj.geometry.centroid
        return [center.x, center.y]

    class Meta:
        model = Boundary
        exclude = ['geometry']
