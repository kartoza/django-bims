# coding=utf8
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.non_biodiversity_layer import NonBiodiversityLayer
from bims.serializers.non_biodiversity_layer_serializer import (
    NonBiodiversityLayerSerializer
)


class NonBiodiversityLayerList(APIView):
    """
    List of all non_biodiversity_layer information
    """

    def get(self, request, format=None):
        return Response(
            NonBiodiversityLayerSerializer(
                NonBiodiversityLayer.objects.all().order_by('order'),
                many=True).data
        )
