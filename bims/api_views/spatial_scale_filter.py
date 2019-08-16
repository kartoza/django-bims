# coding=utf-8
from collections import OrderedDict
from rest_framework.views import APIView, Response
from bims.models import SpatialScale, SpatialScaleGroup, GEO_CLASS_GROUP


class SpatialScaleFilterList(APIView):
    """API for listing all spatial scale filter"""
    SPATIAL_FILTER_GROUPS = OrderedDict([
        ('Geomorphological Zone', {
            'key': 'geomorphological_zone',
            'groups': [
                GEO_CLASS_GROUP
            ]
        }),
        ('Freshwater Ecoregion', {
            'key': 'freshwater_ecoregion',
            'groups': [
                'feow_hydrosheds'
            ]
        }),
        ('Province', {
            'key': 'province',
            'groups': [
                'sa_provinces'
            ]
        }),
        ('Management Area', {
            'key': 'management_area',
            'groups': [
                'water_management_area',
                'sub_wmas'
            ]
        }),
        ('Catchment', {
            'key': 'river_catchment',
            'groups': [
                'primary_catchment_area',
                'secondary_catchment_area',
                'tertiary_catchment_area',
                'quaternary_catchment_area',
                'quinary_catchment_area'
            ]
        }),
        ('SA Ecoregion', {
            'key': 'sa_ecoregion',
            'groups': [
                'eco_region_1',
                'eco_region_2'
            ]
        }),
        ('Critical Biodiversity Area (CBA)', {
            'key': 'cba',
            'groups': [
                'wc_cape_biodiversity_spatial_plan'
            ]
        }),
        ('National Freshwater Ecosystem Priority Area (NFEPA)', {
            'key': 'national_freshwater_ecosystem_priority_area',
            'groups': [
                'nfepa_rivers_2011',
                'nfepa_rivers_fepas_2011',
                'nfepa_wetlands_vegetation',
                'nfepa_fish_sanctuaries_all_species',
                'nfepa_fish_sanctuaries_2011',
                'nfepa_wetlands_2011',
                'nfepa_wetlandcluster_2011'
            ]
        }),
        ('Strategic Water Source Areas', {
            'key': 'strategic_water_source_areas',
            'groups': [
                'surface_swsas',
                'ground_swsas'
            ]
        })
    ])

    SPATIAL_GROUP_UPDATED_NAMES = {
        'eco_region_1': 'SA Ecoregion Level 1',
        'eco_region_2': 'SA Ecoregion Level 2'
    }

    def get_spatial_scale(self, spatial_scale_groups):
        spatial_tree = []
        if not spatial_scale_groups:
            return spatial_tree
        for key, value in self.SPATIAL_FILTER_GROUPS.iteritems():
            spatial_tree_data = {
                'key': value['key'],
                'name': key,
                'children': []
            }
            spatial_scale_groups = SpatialScaleGroup.objects.filter(
                key__in=value['groups']
            ).distinct('id').order_by('id')
            try:
                objects = dict(
                    [(obj.key, obj) for obj in spatial_scale_groups])
                spatial_scale_groups = [
                    objects[key] for key in value['groups']]
            except KeyError:
                pass
            for group in spatial_scale_groups:
                spatial_tree_value = list(
                    SpatialScale.objects.filter(
                        group=group,
                    ).order_by('query').values(
                        'id',
                        'query',
                        'name',
                        'type'
                    )
                )

                spatial_tree_value_sorted = sorted(
                    spatial_tree_value,
                    key=lambda i: (
                        int(i['query'].split(' ')[0])
                        if i['query'].split(' ')[0].isdigit()
                        else i['query'])
                )

                group_name = group.name
                if group.key in self.SPATIAL_GROUP_UPDATED_NAMES:
                    group_name = self.SPATIAL_GROUP_UPDATED_NAMES[group.key]
                spatial_tree_group_data = {
                    'id': group.id,
                    'key': group.key,
                    'name': group_name,
                    'value': spatial_tree_value_sorted
                }
                spatial_tree_data['children'].append(spatial_tree_group_data)

            spatial_tree.append(
                spatial_tree_data
            )
        return spatial_tree

    def get(self, request, *args):
        spatial_scale_groups = SpatialScaleGroup.objects.filter(
            parent__isnull=True
        )
        groups = self.get_spatial_scale(spatial_scale_groups)

        return Response(
            groups
        )
