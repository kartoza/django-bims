from braces.views import SuperuserRequiredMixin
from django.views.generic import TemplateView
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models.location_context_group import (
    LocationContextGroup
)
from bims.utils.uuid import is_uuid


class LocationContextGroupSerializer(serializers.ModelSerializer):

    is_native_layer = serializers.SerializerMethodField()

    def get_is_native_layer(self, obj: LocationContextGroup):
        if obj.key:
            return not is_uuid(obj.key)
        return False

    class Meta:
        model = LocationContextGroup
        fields = '__all__'


class ContextLayersView(SuperuserRequiredMixin, TemplateView):
    template_name = 'context_layers.html'


class ContextLayerGroup(SuperuserRequiredMixin, APIView):

    def post(self, request):
        serializer = LocationContextGroupSerializer(
            data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            group = LocationContextGroup.objects.get(pk=pk)
        except LocationContextGroup.DoesNotExist:
            return Response(
                {'error': 'Group not found'},
                status=status.HTTP_404_NOT_FOUND)

        serializer = LocationContextGroupSerializer(
            group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args):
        location_context_groups = (
            LocationContextGroup.objects.all().order_by('order')
        )
        context_group_data = LocationContextGroupSerializer(
            location_context_groups, many=True
        )
        return Response(context_group_data.data)
