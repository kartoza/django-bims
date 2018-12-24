import json
from bims.models.location_site import LocationSite
from bims.models.river_catchment import RiverCatchment


class RiverCatchmentData(object):

    def __init__(self, value, key, parent=None, child=None):
        self.parent = None
        self.child = []
        self.key = None
        self.value = None

    def add_child(self, river_catchment_data):
        self.child.append(river_catchment_data)


def generate_river_catchments():
    """
    Generate river catchments tree data from geocontext data
    then save the data to a file. This data is used for
    multiple selection in the frontend
    """

    # Get all location site with geocontext data
    context_group_values = 'context_group_values'
    service_registry_values = 'service_registry_values'
    catchment_area_keys = [
        'primary_catchment_area',
        'secondary_catchment_area',
        'tertiary_catchment_area',
        'quaternary_catchment_area'
    ]
    catchment_area_order = {
        'primary_catchment_area': 0,
        'secondary_catchment_area': 1,
        'tertiary_catchment_area': 2,
        'quaternary_catchment_area': 3
    }

    location_sites = LocationSite.objects.filter(
        location_context_document__isnull=False
    )
    processed_data = 0

    river_catchment_all_tree = []

    for location_site in location_sites:
        geocontext_data = json.loads(
            location_site.location_context_document
        )
        if context_group_values not in geocontext_data:
            continue

        context_group = geocontext_data[context_group_values]
        river_data = None
        for context_data in context_group:
            if context_data['key'] == 'water_group':
                river_data = context_data
                break

        if not river_data:
            continue

        if service_registry_values not in river_data:
            continue

        service_registry = river_data[service_registry_values]

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

            if service_data_key in catchment_area_keys:
                # Get order
                catchment_order = catchment_area_order[service_data_key]
                if catchment_order == 0:
                    (
                        river_catchment,
                        created
                    ) = RiverCatchment.objects.get_or_create(
                        key=service_data_key,
                        value=service_data_value
                    )
                    river_catchments_tree[catchment_order] = river_catchment
                else:
                    parent_order = catchment_order - 1
                    if parent_order not in river_catchments_tree:
                        continue
                    river_catchment_parent = river_catchments_tree[
                        parent_order]
                    (
                        river_catchment,
                        created
                    ) = RiverCatchment.objects.get_or_create(
                        parent=river_catchment_parent,
                        key=service_data_key,
                        value=service_data_value
                    )
                    river_catchments_tree[catchment_order] = river_catchment

        processed_data += 1
        print('Data processed = %s/%s' % (processed_data, len(location_sites)))

    print(json.dumps(river_catchment_all_tree))
