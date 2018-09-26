# coding=utf-8
import json
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.user_boundary import UserBoundary
from bims.serializers.boundary_serializer import UserBondarySerializer


class UserBoundaryList(APIView):
    """API for listing boundary."""

    def get(self, request, *args):
        boundaries = UserBoundary.objects.filter(
                user=request.user
        )
        serializer = UserBondarySerializer(boundaries, many=True)
        return Response(serializer.data)
