import json
from bims.models.location_site import LocationSite
from bims.models.river_catchment import RiverCatchment

CONTEXT_GROUP_VALUES = 'context_group_values'
SERVICE_REGISTRY_VALUES = 'service_registry_values'
WATER_GROUP = 'water_group'
CATCHMENT_AREA_ORDER = {
    'primary_catchment_area': 0,
    'secondary_catchment_area': 1,
    'tertiary_catchment_area': 2,
    'quaternary_catchment_area': 3
}


def generate_river_catchments(location_site_id=None):
    """
    Generate river catchments tree data from geocontext data
    then save the data to river_catchment table. This data is used for
    multiple selection in the frontend
    """

    # Get all location site with geocontext data
    location_sites = LocationSite.objects.filter(
        location_context_document__isnull=False
    )
    if location_site_id:
        location_sites.filter(id=location_site_id)
    processed_data = 0

    for location_site in location_sites:
        processed_data += 1
        print('Data processed = %s/%s' % (processed_data, len(location_sites)))
        geocontext_data = json.loads(
            location_site.location_context_document
        )
        if CONTEXT_GROUP_VALUES not in geocontext_data:
            continue

        try:
            context_group = geocontext_data[CONTEXT_GROUP_VALUES]
        except TypeError:
            continue
        river_data = None
        for context_data in context_group:
            if context_data['key'] == WATER_GROUP:
                river_data = context_data
                break

        if not river_data:
            continue

        if SERVICE_REGISTRY_VALUES not in river_data:
            continue

        service_registry = river_data[SERVICE_REGISTRY_VALUES]

        river_catchments_tree = {}

        for service_data in service_registry:
            if 'key' not in service_data:
                continue
            if 'value' not in service_data:
                continue
            service_data_key = service_data['key']
            service_data_value = service_data['value']

            if not service_data_key or not service_data_value:
                continue

            if service_data_key in CATCHMENT_AREA_ORDER:
                # Get order
                catchment_order = CATCHMENT_AREA_ORDER[service_data_key]
                extra_fields = {}
                if catchment_order > 0:
                    parent_order = catchment_order - 1
                    if parent_order not in river_catchments_tree:
                        continue
                    river_catchment_parent = river_catchments_tree[
                        parent_order]
                    extra_fields['parent'] = river_catchment_parent

                (
                    river_catchment,
                    created
                ) = RiverCatchment.objects.get_or_create(
                    key=service_data_key,
                    value=service_data_value,
                    **extra_fields
                )
                river_catchment.location_sites.add(location_site)
                river_catchments_tree[catchment_order] = river_catchment


def get_river_catchment_tree(parent=None):
    """
    Get all the river catchment from table then return it
    as dict tree
    :return: dict
    """
    river_catchments_dict = []
    if parent:
        river_catchments = RiverCatchment.objects.filter(
            parent=parent
        )
    else:
        river_catchments = RiverCatchment.objects.filter(
            parent__isnull=True
        )
    for river_catchment in river_catchments:
        river_catchments_dict.append({
            'key': river_catchment.key,
            'value': river_catchment.value,
            'children': get_river_catchment_tree(river_catchment)
        })

    return river_catchments_dict


def get_river_catchment_site(location_site):
    """
    Read from location context document of location site,
    the return all river catchment values.

    :param location_site: LocationSite object
    :return: array of river catchment value
    """
    if not location_site.location_context_document:
        return []

    river_catchment_values = []
    geocontext_data = json.loads(
        location_site.location_context_document
    )
    if CONTEXT_GROUP_VALUES not in geocontext_data:
        return river_catchment_values

    context_group = geocontext_data[CONTEXT_GROUP_VALUES]
    river_data = None
    for context_data in context_group:
        if context_data['key'] == WATER_GROUP:
            river_data = context_data
            break

    if not river_data:
        return river_catchment_values

    if SERVICE_REGISTRY_VALUES not in river_data:
        return river_catchment_values

    service_registry = river_data[SERVICE_REGISTRY_VALUES]
    for service_data in service_registry:
        if 'key' not in service_data:
            continue
        if 'value' not in service_data:
            continue
        service_data_key = service_data['key']
        service_data_value = service_data['value']

        if not service_data_key or not service_data_value:
            continue

        if service_data_key in CATCHMENT_AREA_ORDER:
            river_catchment_values.append(service_data_value)

    return river_catchment_values
