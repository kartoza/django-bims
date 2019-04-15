# coding=utf-8
import copy
from rest_framework.views import APIView, Response
from bims.models import SpatialScale, SpatialScaleGroup
from bims.views.fish_form import RIVER_CATCHMENT_ORDER


class SpatialScaleFilterList(APIView):
    """API for listing all spatial scale filter"""
    SPATIAL_FILTER_TO_EXCLUDE = [
        'Geomorphological Zones',
        'Ecological Region',
        'Geomorphological zones',
    ]

    def get_spatial_scale(self, spatial_scale_groups):
        spatial_tree = []
        if not spatial_scale_groups:
            return spatial_tree
        for spatial_scale in spatial_scale_groups:
            spatial_scale_children = SpatialScaleGroup.objects.filter(
                parent=spatial_scale
            ).exclude(name__in=self.SPATIAL_FILTER_TO_EXCLUDE)
            if spatial_scale.name.lower() == (
                'geomorphological zones - recoded'):
                spatial_scale.name = 'Geomorphological Zones'

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
                        group=spatial_scale,
                        type='select'
                    ).values(
                        'id',
                        'query',
                        'name',
                        'type'
                    )
                )
            spatial_tree.append(spatial_tree_data)
        return spatial_tree

    def order_river_catchments(self, spatial_scale_list):
        """
        Order river catchment filter
        :param spatial_scale_list: list of spatial scale filter
        """
        river_catchment_order = copy.deepcopy(RIVER_CATCHMENT_ORDER)
        river_catchment_order.reverse()
        river_catchment_order.append('nfepa_wetlands')
        for group in spatial_scale_list:
            if group['key'] == 'water_group':
                ordered_river = []
                for river_order in river_catchment_order:
                    for group_child in group['children']:
                        if group_child['key'] == river_order:
                            ordered_river.append(group_child)
                            break
                group['children'] = ordered_river

    def fix_spatial_filters(self, spatial_scale_list):
        new_spatial_list = []
        for group in spatial_scale_list:
            if 'value' in group and not group['value']:
                continue
            new_spatial_list.append(group)
        return new_spatial_list

    def get(self, request, *args):
        spatial_scale_groups = SpatialScaleGroup.objects.filter(
            parent__isnull=True
        )
        groups = self.get_spatial_scale(spatial_scale_groups)
        self.order_river_catchments(groups)
        groups = self.fix_spatial_filters(groups)

        return Response(
            groups
        )
