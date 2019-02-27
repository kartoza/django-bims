# coding=utf-8
from rest_framework.views import APIView, Response
from bims.models import SpatialScale, SpatialScaleGroup


class SpatialScaleFilterList(APIView):
    """API for listing all spatial scale filter"""

    def get_spatial_scale(self, spatial_scale_groups):
        spatial_tree = []
        if not spatial_scale_groups:
            return spatial_tree
        for spatial_scale in spatial_scale_groups:
            spatial_scale_children = SpatialScaleGroup.objects.filter(
                parent=spatial_scale
            )
            spatial_tree_data = {
                'id': spatial_scale.id,
                'key': spatial_scale.key,
                'name': spatial_scale.name,
            }
            if spatial_scale_children:
                spatial_tree_data['children'] = (
                    self.get_spatial_scale(spatial_scale_children)
                )
            else:
                spatial_tree_data['value'] = list(
                    SpatialScale.objects.filter(
                        group=spatial_scale
                    ).values(
                        'id',
                        'query',
                        'name',
                        'type'
                    )
                )
            spatial_tree.append(spatial_tree_data)
        return spatial_tree

    def get(self, request, *args):
        spatial_scale_groups = SpatialScaleGroup.objects.filter(
            parent__isnull=True
        )
        groups = self.get_spatial_scale(spatial_scale_groups)
        return Response(
            groups
        )
