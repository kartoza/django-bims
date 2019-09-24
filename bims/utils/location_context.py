from bims.models.spatial_scale import SpatialScale
from bims.models.spatial_scale_group import SpatialScaleGroup


def array_to_dict(array, key_name='key'):
    dictionary = {}
    if not isinstance(array, list):
        return dictionary
    for data_dict in array:
        try:
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
            dictionary[data_dict[key_name]] = data_dict
        except (AttributeError, KeyError, TypeError):
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
            try:
                SpatialScale.objects.get_or_create(
                    group=spatial_scale_group,
                    key=context_group['key'],
                    name=context_group['name'],
                    type=spatial_type,
                    query=spatial_query
                )
            except SpatialScale.MultipleObjectsReturned:
                # shouldn't be happen
                spatial_scales = SpatialScale.objects.filter(
                    group=spatial_scale_group,
                    key=context_group['key'],
                    name=context_group['name'],
                    type=spatial_type,
                    query=spatial_query
                )
                SpatialScale.objects.filter(
                    id__in=spatial_scales.values_list('id', flat=True)[1:]
                ).delete()
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
