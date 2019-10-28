# coding=utf-8
import os
import json
from celery import shared_task
from collections import OrderedDict
from django.db.models import Case, When, CharField, Value, F
from django.conf import settings
from bims.models import GEO_CLASS_GROUP, LocationContext
from bims.utils.celery import single_instance_task
from bims.utils.logger import log


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
        'key': 'political_boundary_group',
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
    ('Critical Biodiversity Area (CBA) National', {
        'key': 'cba_national',
        'groups': [
            'national_cba_layer',
            'national_esa',
            'npa_layer',
        ]
    }),
    ('Critical Biodiversity Area (CBA) Provincial', {
        'key': 'cba_provincial',
        'groups': [
            'limpopo_cba',
            'free_state_cba',
            'gauteng_cba',
            'mpumalanga_cba',
            'northern_cape_cba',
            'north_west_cba',
            'kzn_cba',
            'ec_cba',
            'wc_cba'
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

LAYER_NAMES = {
    'surface_swsas': 'surface_strategic_water_source_2017',
    'nfepa_rivers_fepas_2011': 'rivers_nfepa',
    'water_management_area': 'water_management_areas',
    GEO_CLASS_GROUP: 'geoclass',
    'national_cba_layer': 'cba_national_mview',
}


@shared_task(name='bims.tasks.generate_spatial_scale_filter', queue='update')
@single_instance_task(60 * 10)
def generate_spatial_scale_filter(file_path=None):
    spatial_tree = []
    for key, value in SPATIAL_FILTER_GROUPS.iteritems():
        spatial_tree_data = {
            'key': value['key'],
            'name': key,
            'children': []
        }
        whens = [
            When(
                key=k, then=Value(v)
            ) for k, v in SPATIAL_GROUP_UPDATED_NAMES.iteritems()
        ]
        for group in value['groups']:
            location_contexts = LocationContext.objects.filter(
                key=group
            ).distinct('value').order_by('value').exclude(value='None')
            if not location_contexts:
                continue
            spatial_tree_value = list(
                location_contexts.values(
                    'key',
                ).annotate(
                    name=Case(
                        *whens,
                        default='name',
                        output_field=CharField()
                    ),
                    query=F('value')
                ))
            spatial_tree_value_sorted = sorted(
                spatial_tree_value,
                key=lambda i: (
                    int(i['query'].split(' ')[0])
                    if i['query'].split(' ')[0].isdigit()
                    else i['query'])
            )
            layer_name = group
            if layer_name in LAYER_NAMES:
                layer_name = LAYER_NAMES[layer_name]
            spatial_tree_children = {
                'key': group,
                'name': location_contexts[0].name,
                'value': spatial_tree_value_sorted,
                'layer_name': layer_name
            }
            spatial_tree_data['children'].append(spatial_tree_children)

        spatial_tree.append(
            spatial_tree_data
        )

    if spatial_tree:
        if not file_path:
            file_name = 'spatial_scale_filter_list.txt'
            file_path = os.path.join(
                settings.MEDIA_ROOT,
                file_name
            )
        log(file_path)
        with open(file_path, 'w') as file_handle:
            json.dump(spatial_tree, file_handle)
