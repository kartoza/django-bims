import hashlib
import json
from django.contrib.gis.db import models
from bims.models.location_site import (
    location_site_post_save_handler,
    LocationSite
)
from bims.models.spatial_scale import SpatialScale
from bims.models.spatial_scale_group import SpatialScaleGroup
from bims.utils.logger import log


def array_to_dict(array, key_name='key'):
    dictionary = {}
    for data_dict in array:
        for data_key, data_value in data_dict.iteritems():
            if isinstance(data_value, list):
                formatted_dict = array_to_dict(data_value)
                if formatted_dict:
                    data_dict[data_key] = formatted_dict
            elif data_value:
                if isinstance(data_value, float):
                    continue
                if data_value.isdigit():
                    data_dict[data_key] = int(data_value)
                else:
                    try:
                        data_dict[data_key] = float(data_value)
                    except ValueError:
                        continue
            else:
                continue
        try:
            dictionary[data_dict[key_name]] = data_dict
        except KeyError:
            continue
    return dictionary


def process_spatial_scale_data(location_context_data, group=None):
    for context_group_value in location_context_data:
        try:
            context_group = location_context_data[context_group_value]
        except TypeError:
            return
        if 'value' in context_group:
            if not context_group['value']:
                continue
            spatial_type = 'select'
            spatial_query = context_group['value']
            spatial_scale_group, created = (
                SpatialScaleGroup.objects.get_or_create(
                    key=context_group['key'],
                    name=context_group['name'],
                    parent=group
                ))
            spatial_scale, spatial_created = (
                SpatialScale.objects.get_or_create(
                    group=spatial_scale_group,
                    key=context_group['key'],
                    name=context_group['name'],
                    type=spatial_type,
                    query=spatial_query
                )
            )
        else:
            spatial_scale_group, created = (
                SpatialScaleGroup.objects.get_or_create(
                    key=context_group['key'],
                    name=context_group['name'],
                    parent=group
                ))
            if 'service_registry_values' in context_group:
                process_spatial_scale_data(
                    context_group['service_registry_values'],
                    group=spatial_scale_group
                )


def format_location_context(location_site_id, force_update=False):
    try:
        location_site = LocationSite.objects.get(
            id=location_site_id
        )
    except LocationSite.DoesNotExist:
        log('LocationSite Does Not Exist', 'debug')
        return

    if not location_site.location_context_document:
        log('LocationSite context document does not exist', 'debug')
        return

    location_context = json.loads(location_site.location_context_document)
    hash_string = hashlib.md5(
        location_site.location_context_document
    ).hexdigest()
    formatted = {}

    if location_site.location_context and not force_update:
        formatted_location_context = json.loads(
            location_site.location_context
        )

        if not location_site.original_geomorphological:
            try:
                context_geo = formatted_location_context[
                    'context_group_values'][
                    'eco_geo_group']['service_registry_values'][
                    'geo_class_recoded']['value']
                models.signals.post_save.disconnect(
                    location_site_post_save_handler,
                )
                location_site.original_geomorphological = context_geo
                location_site.save()
                models.signals.post_save.connect(
                    location_site_post_save_handler,
                )
            except KeyError:
                pass

        if 'hash' in formatted_location_context:
            if formatted_location_context['hash'] == hash_string:
                process_spatial_scale_data(
                    formatted_location_context['context_group_values']
                )
                if location_site.refined_geomorphological:
                    # Update geo value in geocontext data
                    try:
                        context_geo = formatted_location_context[
                            'context_group_values'][
                            'eco_geo_group']['service_registry_values'][
                            'geo_class_recoded']['value']
                        if (
                                context_geo ==
                                location_site.refined_geomorphological):
                            log('Formatted location context already exist')
                            return
                    except KeyError:
                        log('Formatted location context already exist')
                        return
                else:
                    log('Formatted location context already exist')
                    return

    if not isinstance(location_context, dict):
        return
    for context_key, context_value in location_context.iteritems():
        if isinstance(context_value, list):
            formatted[context_key] = array_to_dict(
                context_value, key_name='key')
        else:
            formatted[context_key] = context_value

    models.signals.post_save.disconnect(
        location_site_post_save_handler,
    )

    if not location_site.original_geomorphological:
        try:
            context_geo = formatted[
                'context_group_values'][
                'eco_geo_group']['service_registry_values'][
                'geo_class_recoded']['value']
            location_site.original_geomorphological = context_geo
        except KeyError:
            pass

    if location_site.refined_geomorphological:
        try:
            formatted['context_group_values'][
                'eco_geo_group']['service_registry_values'][
                'geo_class_recoded']['value'] = (
                location_site.refined_geomorphological
            )
        except KeyError:
            pass

    process_spatial_scale_data(
        formatted['context_group_values']
    )
    formatted['hash'] = hash_string
    location_site.location_context = formatted
    location_site.save()
    log('Location context formatted', 'info')

    models.signals.post_save.connect(
        location_site_post_save_handler,
    )
