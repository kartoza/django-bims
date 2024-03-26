# coding=utf-8
import json
import logging
import os

from celery import shared_task
from collections import OrderedDict

from django.conf import settings
from django.core.cache import cache
from django.db.models import F
from django.utils.text import slugify

from bims.utils.celery import single_instance_task

logger = logging.getLogger(__name__)
SPATIAL_SCALE_FILTER_FILE = 'spatial_scale_filter.txt'


SPATIAL_FILTER_GROUPS = OrderedDict([
    ('Geomorphological Zone', {
        'key': 'geomorphological_zone',
        'groups': [
            'geo_class_recoded'
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
    'geo_class_recoded': 'geoclass',
    'national_cba_layer': 'cba_national_mview',
}


@shared_task(
    name='bims.tasks.generate_filters',
    queue='geocontext'
)
@single_instance_task(60 * 10)
def generate_spatial_scale_filter_if_empty():
    from bims.tasks.source_reference import generate_source_reference_filter
    from bims.api_views.module_summary import ModuleSummary
    get_spatial_scale_filter()
    generate_source_reference_filter()

    module_summary_api = ModuleSummary()
    module_summary_api.call_summary_data_in_background()


@shared_task(
    name='bims.tasks.generate_spatial_scale_filter', queue='geocontext')
@single_instance_task(60 * 10)
def generate_spatial_scale_filter():
    from bims.models import (
        LocationContext, LocationContextFilter, LocationContextFilterGroupOrder
    )
    spatial_tree = []
    location_context_filters = LocationContextFilter.objects.all(
    ).order_by(
        'display_order',
    )
    for location_context_filter in location_context_filters:
        spatial_tree_data = {
            'name': location_context_filter.title,
            'key': slugify(location_context_filter.title),
            'children': []
        }
        for group in location_context_filter.location_context_groups.all(
        ).order_by('locationcontextfiltergrouporder__group_display_order'):
            location_contexts = LocationContext.objects.filter(
                group=group
            ).distinct('value').order_by('value').exclude(value='None')
            if not location_contexts:
                continue

            location_filter_group_order = (
                LocationContextFilterGroupOrder.objects.filter(
                    filter_id=location_context_filter.id,
                    group_id=group.id,
                    is_hidden_in_spatial_filter=False
                ).first()
            )

            if not location_filter_group_order:
                continue

            spatial_tree_value_sorted = []
            if not location_filter_group_order.use_autocomplete_in_filter:
                spatial_tree_value = list(
                    location_contexts.annotate(
                        query=F('value'),
                        key=F('group__key')
                    ).values('query', 'key'))
                try:
                    # Check empty query
                    for index, value in enumerate(spatial_tree_value):
                        if value['query'] == "":
                            del(spatial_tree_value[index])

                    # Sort values that have a number prefix, e.g. "1 - Limpopo."
                    spatial_tree_value_sorted = sorted(
                        spatial_tree_value,
                        key=lambda i: (
                            int(i['query'].split(' ')[0])
                            if i['query'].split(' ')[0].isdigit()
                            else 99)
                    )
                except TypeError:
                    continue

            layer_name = group.layer_name
            spatial_tree_children = {
                'key': group.key,
                'name': group.name,
                'value': spatial_tree_value_sorted,
                'autocomplete': location_filter_group_order.use_autocomplete_in_filter,
                'layer_name': layer_name,
                'wms_url': group.wms_url,
                'wms_format': group.wms_format,
                'layer_identifier': group.layer_identifier,
            }
            spatial_tree_data['children'].append(spatial_tree_children)

        spatial_tree.append(
            spatial_tree_data
        )

    if spatial_tree:
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            SPATIAL_SCALE_FILTER_FILE
        )
        with open(file_path, 'w') as file_handle:
            json.dump(spatial_tree, file_handle)


def get_spatial_scale_filter():
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        SPATIAL_SCALE_FILTER_FILE
    )
    if not os.path.exists(file_path):
        generate_spatial_scale_filter()
    with open(file_path, 'r') as file_handler:
        filter_data = file_handler.read()
    if filter_data:
        return json.loads(filter_data)
    else:
        return []
