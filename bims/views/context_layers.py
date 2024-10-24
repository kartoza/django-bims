from braces.views import SuperuserRequiredMixin
from django.views.generic import TemplateView
from django_tenants.utils import get_tenant
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from preferences import preferences

from bims.models.geocontext_setting import GeocontextSetting
from bims.models.location_context_group import (
    LocationContextGroup
)
from bims.models.location_context_filter import (
    LocationContextFilter
)
from bims.models.location_context_filter_group_order import (
    LocationContextFilterGroupOrder
)
from bims.utils.uuid import is_uuid
from bims.tasks.location_context import generate_spatial_scale_filter
from cloud_native_gis.models import Layer
from cloud_native_gis.serializer.layer import LayerSerializer


class NativeLayerSerializer(LayerSerializer):
    class Meta:
        model = Layer
        fields = '__all__'


class LocationContextGroupSerializer(serializers.ModelSerializer):

    is_native_layer = serializers.SerializerMethodField()
    native_layer_name = serializers.SerializerMethodField()

    def get_native_layer_name(self, obj: LocationContextGroup):
        if obj.key and is_uuid(obj.key):
            layer = Layer.objects.get(unique_id=obj.key)
            return layer.name
        return ''

    def get_is_native_layer(self, obj: LocationContextGroup):
        if obj.key:
            return is_uuid(obj.key)
        return False

    class Meta:
        model = LocationContextGroup
        fields = '__all__'


class LocationFilterGroupSerializer(serializers.ModelSerializer):
    group = LocationContextGroupSerializer(many=False)

    class Meta:
        model = LocationContextFilterGroupOrder
        fields = '__all__'


class LocationFilterSerializer(serializers.ModelSerializer):
    location_context_groups = serializers.SerializerMethodField()

    def get_location_context_groups(self, obj):
        filter_group_orders = (
            LocationContextFilterGroupOrder.objects.filter(filter=obj)
        )
        return (
            LocationFilterGroupSerializer(
                filter_group_orders,
                many=True).data
        )

    class Meta:
        model = LocationContextFilter
        exclude = ['site',]



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


class ContextFilter(SuperuserRequiredMixin, APIView):
    def get(self, request, *args):
        context_filters = (
            LocationContextFilter.objects.all().order_by(
                'display_order')
        )
        context_filter_data = LocationFilterSerializer(
            context_filters, many=True
        )
        return Response(context_filter_data.data)

    def post(self, request, *args):
        data = request.data
        serializer = LocationFilterSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Filter created successfully.",
                    "filter": serializer.data
                 }, status=201)
        else:
            return Response(serializer.errors, status=400)

    def delete(self, request, *args):
        filter_id = request.query_params.get('filter_id')

        if not filter_id:
            return Response({"error": "filter_id is required."}, status=400)

        filter_to_delete = LocationContextFilter.objects.filter(
            id=filter_id
        )
        if filter_to_delete.exists():
            filter_to_delete.delete()
            return Response({
                "message": f"Filter {filter_id} deleted successfully."},
                status=204)
        else:
            return Response({
                "error": f"Filter with id {filter_id} not found."}, status=404)

    def put(self, request, *args):
        """Update the order of context filters and groups."""
        data = request.data
        filters_data = data.get('filters', [])
        groups_data = data.get('groups', {})

        # Update filter order
        for filter_data in filters_data:
            filter_id = filter_data.get('id')
            new_order = filter_data.get('display_order')
            updated_data = {
                'display_order': new_order
            }

            filter_title = filter_data.get('title')
            if filter_title:
                updated_data['title'] = filter_title

            LocationContextFilter.objects.filter(
                id=filter_id).update(
                    **updated_data
            )

        # Update group order within each filter
        for filter_id, groups in groups_data.items():
            for group_data in groups:
                group_id = group_data.get('id')
                new_group_order = group_data.get('group_display_order')
                remove = group_data.get('remove', False)
                context_filter_group = LocationContextFilterGroupOrder.objects.filter(
                    filter_id=filter_id,
                    group_id=group_id
                )
                if context_filter_group.exists():
                    if remove:
                        context_filter_group.delete()
                    else:
                        context_filter_group.update(
                            group_display_order=new_group_order)
                else:
                    if not remove:
                        LocationContextFilterGroupOrder.objects.create(
                            filter_id=filter_id,
                            group_id=group_id,
                            group_display_order=new_group_order
                        )

        tenant_id = get_tenant(request).id
        generate_spatial_scale_filter.delay(tenant_id)

        return Response(
            {"message": "Order updated successfully."}, status=200)


class CloudNativeLayerAutoCompleteAPI(APIView):
    def get(self, request, *args):
        query = request.query_params.get('q', '')
        layers = Layer.objects.filter(
            name__icontains=query
        )
        serializer = NativeLayerSerializer(
            layers, many=True, context={
            'request': request
        })
        return Response(serializer.data)


class LayerSummarySerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()

    def get_attributes(self, obj: Layer):
        return obj.attribute_names
    class Meta:
        model = Layer
        fields = [
            'name', 'id', 'is_ready',
            'unique_id', 'attributes']


class LocationContextGroupSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationContextGroup
        fields = [
            'id', 'name', 'key', 'geocontext_group_key'
        ]


class ContextLayerKeys(SuperuserRequiredMixin, APIView):
    """List all geocontext keys used to fetch spatial filters or native layer keys."""

    def post(self, request, *args):
        data = request.data
        new_key = data.get('key', '')
        geocontext_setting = GeocontextSetting.objects.get(
            id=preferences.GeocontextSetting.id
        )

        context_keys = (
            geocontext_setting.geocontext_keys.split(',')
        )

        if new_key not in context_keys:
            context_keys.append(new_key)
            geocontext_setting.geocontext_keys = ','.join(context_keys)
            geocontext_setting.save()
            return Response(
                {
                    "message": "Context key added successfully.",
                }, status=201)
        else:
            return Response(
                {
                    "message": "Context key already exists.",
                }
                , status=400)

    def delete(self, request, *args):
        key = request.query_params.get('key')

        if not key:
            return Response({"error": "key is required."}, status=400)

        geocontext_setting = GeocontextSetting.objects.get(
            id=preferences.GeocontextSetting.id
        )

        context_keys = (
            geocontext_setting.geocontext_keys.split(',')
        )
        if key in context_keys:
            context_keys.remove(key)
            geocontext_setting.geocontext_keys = ','.join(context_keys)
            geocontext_setting.save()

            return Response({
                "message": f"Context key {key} deleted successfully."},
                status=204)
        else:
            return Response({
                "error": f"Context with key {key} not found."}, status=404)

    def get(self, request, *args):
        context_keys = (
            preferences.GeocontextSetting.geocontext_keys.split(',')
        )
        context_key_data = []
        for key in context_keys:
            if ':' in key:
                uuid_key = key.split(':')[0]
                cloud_native_layer = Layer.objects.filter(
                    unique_id=uuid_key
                )
                if cloud_native_layer.exists():
                    layer_summary_data = (
                        LayerSummarySerializer(
                            cloud_native_layer.first(),
                            many=False,
                        ).data
                    )
                    layer_summary_data['attribute_used'] = (
                        key.split(':')[-1].strip()
                    )
                    layer_summary_data['key'] = key
                    layer_summary_data['type'] = 'native_layer'
                    context_key_data.append(
                        layer_summary_data
                    )
                    continue
            else:
                location_context_group = LocationContextGroup.objects.filter(
                    geocontext_group_key=key
                )
                if location_context_group.exists():
                    context_key_data.append({
                        'key': key,
                        'type': 'geocontext',
                        'groups': (
                            LocationContextGroupSummarySerializer(
                                location_context_group,
                                many=True
                            ).data
                        )
                    })
                    continue

            context_key_data.append({
                'key': key,
                'type': 'geocontext'
            })
        return Response(
            context_key_data
        )
