import json
from django.db import models

from bims.models import (
    location_site_post_save_handler,
    LocationSite
)


def get_context_data_value(context_data, value_to_find):
    for single_context_data in context_data:
        try:
            if single_context_data['key'] == value_to_find:
                return single_context_data['value']
        except KeyError:
            continue
    return ''


def allocate_site_codes_from_river(update_site_code=True, location_id=None):
    """
    Allocate site codes to the existing location site
    :param update_site_code: should also update existed site code
    :param location_id: location id to allocate site codes, if None, allocate
    all site
    """
    models.signals.post_save.disconnect(
        location_site_post_save_handler
    )

    if location_id:
        location_sites = LocationSite.objects.filter(id=location_id)
    else:
        location_sites = LocationSite.objects.all()

    # Add site code with the context data
    location_site_with_context = location_sites.objects.filter(
        location_context_document__isnull=False
    ).order_by('id')

    if not update_site_code:
        location_site_with_context = location_site_with_context.exclude(
            site_code__isnull=False
        )

    for location_site in location_site_with_context:
        print('Update location site for %s' % location_site.name)
        site_code = ''
        context_data = json.loads(location_site.location_context_document)
        secondary_catchment = ''
        river_name = ''

        for context_group in context_data['context_group_values']:
            context_group_data = context_group['service_registry_values']

            if 'key' not in context_group:
                continue

            if context_group['key'] == 'water_group':
                # Find secondary catchment area
                secondary_catchment = (
                    get_context_data_value(
                        context_group_data,
                        'secondary_catchment_area'
                    )
                )
                # Find river name
                river_name = get_context_data_value(
                    context_group_data,
                    'water_management_area'
                )
                # Get first four letters of the river name
                river_name_list = river_name.split(' ')
                river_name = river_name_list[len(river_name_list) - 1]
                river_name = river_name[:4].upper()

        if secondary_catchment:
            site_code += secondary_catchment
        else:
            continue

        if river_name:
            site_code += river_name
        else:
            continue

        # Add hyphen
        site_code += '-'

        # Add five letters describing location e.g. 00001
        existed_location_sites = LocationSite.objects.filter(
            site_code__contains=site_code
        )
        site_code_number = len(existed_location_sites) + 1
        site_code_string = str(site_code_number).zfill(5)
        site_code += site_code_string

        if location_site.site_code and not location_site.legacy_site_code:
            location_site.legacy_site_code = location_site.site_code

        location_site.site_code = site_code
        location_site.save()

    models.signals.post_save.connect(
        location_site_post_save_handler
    )
