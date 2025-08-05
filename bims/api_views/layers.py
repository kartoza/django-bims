import json

from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from cloud_native_gis.models import Layer
from cloud_native_gis.serializer.layer import LayerSerializer


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


class LayerByUUIDView(APIView):
    """View to get a layer by UUID."""

    def get(self, request, uuid):
        layer = get_object_or_404(Layer, unique_id=uuid)
        serializer = LayerSerializer(
            layer, context={'request': request})
        return Response(
            serializer.data,
            status=status.HTTP_200_OK)
