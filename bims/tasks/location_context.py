# coding=utf-8
import json
import logging
import os

from celery import shared_task
from collections import OrderedDict

from django.conf import settings
from django.db.models import F
from django.utils.text import slugify

from bims.utils.celery import single_instance_task

logger = logging.getLogger(__name__)
SPATIAL_SCALE_FILTER_FILE = 'spatial_scale_filter.txt'
SPATIAL_SCALE_FILTER_DIR = 'spatial_scale'


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
    queue='geocontext',
    ignore_result=True
)
def generate_filters():
    from bims.tasks.source_reference import generate_source_reference_filter
    from bims.api_views.module_summary import ModuleSummary
    from django.contrib.sites.models import Site
    get_spatial_scale_filter()
    generate_source_reference_filter()

    all_sites = Site.objects.all()
    for site in all_sites:
        module_summary_api = ModuleSummary()
        module_summary_api.call_summary_data_in_background(site)


@shared_task(
    name='bims.tasks.generate_filters_in_all_schemas',
    queue='geocontext',
    ignore_result=True
)
def generate_filters_in_all_schemas():
    from django_tenants.utils import get_tenant_model, tenant_context

    for tenant in get_tenant_model().objects.exclude(schema_name='public'):
        with tenant_context(tenant):
            generate_filters.delay()


@shared_task(
    name='bims.tasks.generate_spatial_scale_filter',
    queue='geocontext',
    ignore_result=True)
@single_instance_task(60 * 10)
def generate_spatial_scale_filter(current_site_id=None):
    from django.contrib.sites.models import Site
    from bims.models import (
        LocationContext, LocationContextFilter, LocationContextFilterGroupOrder
    )
    if not current_site_id:
        sites = Site.objects.all()
        for site in sites:
            generate_spatial_scale_filter(site.id)
        return

    spatial_tree = []
    location_context_filters = LocationContextFilter.objects.all()
    if current_site_id:
        location_context_filters = location_context_filters.filter(
            locationcontextfiltergrouporder__site_id=current_site_id
        ).distinct()
    location_context_filters = location_context_filters.order_by(
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
                    is_hidden_in_spatial_filter=False,
                    site_id=current_site_id
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

    if spatial_tree and current_site_id:
        spatial_dir = os.path.join(
            settings.MEDIA_ROOT,
            SPATIAL_SCALE_FILTER_DIR,
        )
        if not os.path.exists(spatial_dir):
            os.mkdir(spatial_dir)
        file_dir = os.path.join(
            spatial_dir,
            str(current_site_id)
        )
        if not os.path.exists(file_dir):
            os.mkdir(file_dir)
        file_path = os.path.join(
            file_dir,
            SPATIAL_SCALE_FILTER_FILE
        )
        with open(file_path, 'w') as file_handle:
            json.dump(spatial_tree, file_handle)


def get_spatial_scale_filter():
    from django.contrib.sites.models import Site
    current_site = Site.objects.get_current()
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        SPATIAL_SCALE_FILTER_DIR,
        str(current_site.id),
        SPATIAL_SCALE_FILTER_FILE
    )
    if not os.path.exists(file_path):
        generate_spatial_scale_filter(current_site.id)
    with open(file_path, 'r') as file_handler:
        filter_data = file_handler.read()
    if filter_data:
        return json.loads(filter_data)
    else:
        return []
