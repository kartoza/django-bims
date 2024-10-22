import json

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from cloud_native_gis.models import Layer


class CloudNativeLayerSerializer(serializers.ModelSerializer):

    attributes = serializers.SerializerMethodField()

    def get_attributes(self, obj: Layer):
        return obj.attribute_names

    class Meta:
        model = Layer
        fields = [
            'id', 'unique_id',
            'name', 'abstract',
            'attributes', 'default_style'
        ]


class CloudNativeLayerList(APIView):
    """API for listing all cloud native layers."""

    def get(self, request, *args):
        layers = Layer.objects.all()
        layers_data = CloudNativeLayerSerializer(
            layers,
            many=True
        ).data
        return Response(
            layers_data
        )
