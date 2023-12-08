# coding=utf-8
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from bims.models.user_boundary import UserBoundary
from bims.serializers.boundary_serializer import UserDetailBoundarySerializer
from bims.serializers.user_boundary import UserBoundarySerializer


class UserBoundaryDetailList(APIView):
    """API for listing user boundary with geometry."""

    def get(self, request, *args):
        boundaries = UserBoundary.objects.filter(
                user=request.user
        )
        serializer = UserDetailBoundarySerializer(
            boundaries, many=True
        )
        return Response(serializer.data)


class UserBoundaryList(LoginRequiredMixin, APIView):
    """API for listing user boundary without geometry."""

    def get(self, request):

        user_boundaries = UserBoundary.objects.filter(
            user=request.user
        )
        return Response(
            UserBoundarySerializer(
                user_boundaries, many=True).data)


class UserBoundaryDetail(LoginRequiredMixin, APIView):
    """API for a user boundary with geometry."""

    def get(self, request, *args, **kwargs):
        user_boundary_id = kwargs.get('id')
        if not user_boundary_id:
            raise Http404('Missing id')
        user_boundary = get_object_or_404(
            UserBoundary,
            pk=user_boundary_id
        )
        return Response(
            UserDetailBoundarySerializer(user_boundary).data)


class DeleteUserBoundary(LoginRequiredMixin, APIView):
    """API for deleting a user boundary by id"""

    def delete(self, request, *args, **kwargs):
        user_boundary_id = kwargs.get('id')
        if not user_boundary_id:
            raise Http404('Missing id')

        user_boundary = get_object_or_404(
            UserBoundary,
            pk=user_boundary_id,
            user_id=request.user.id
        )
        user_boundary.delete()

        return Response(status=HTTP_204_NO_CONTENT)
