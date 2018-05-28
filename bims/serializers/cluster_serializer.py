import json
from rest_framework import serializers
from bims.models.cluster import Cluster


class ClusterSerializer(serializers.ModelSerializer):
    """
    Serializer for cluster model.
    """
    details = serializers.SerializerMethodField()

    def get_details(self, obj):
        try:
            return json.loads(obj.details)
        except json.decoder.JSONDecodeError:
            return 'details is error'

    class Meta:
        model = Cluster
        exclude = ['boundary']
