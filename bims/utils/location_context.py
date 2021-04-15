import operator
from functools import reduce
from django.db.models import Q
from django.db.models.fields.related import ForeignObjectRel
from bims.models.spatial_scale import SpatialScale
from bims.models.spatial_scale_group import SpatialScaleGroup
from bims.models.location_site import LocationSite, generate_site_code
from bims.models.location_context import LocationContext
from bims.utils.logger import log
from preferences import preferences


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


def get_location_context_data(
        group_keys=None,
        site_id=None,
        only_empty=False,
        should_generate_site_code=False):
    """
    Get the location context for specific site or all sites
    :param group_keys: Group keys used to fetch geocontext data
        (separated by comma), if empty then use geocontext keys from
        site setting
    :param site_id: Sites that will be updated, can be multiple sites
        if separated by comma. If empty then update all sites
    :param only_empty: Only add empty missing context data
    :param should_generate_site_code: Generate the site code after updating
    :return:
    """
    # Get location context data from GeoContext

    if not group_keys:
        group_keys = preferences.SiteSetting.geocontext_keys.split(',')
    else:
        if not isinstance(group_keys, list):
            group_keys = group_keys.split(',')

    if site_id:
        location_sites = LocationSite.objects.filter(id__in=site_id.split(','))
    else:
        location_sites = LocationSite.objects.all()

    if only_empty:
        location_sites = location_sites.exclude(
            reduce(operator.and_, (
                Q(locationcontext__group__geocontext_group_key=x)
                for x in group_keys)
                   ))
    num = len(location_sites)
    i = 1

    if num == 0:
        log('No locations with applied filters were found')
        return

    for location_site in location_sites:
        log('Updating %s of %s, %s' % (i, num, location_site.name))
        i += 1
        all_context = None
        if only_empty:
            try:
                all_context = list(
                    LocationContext.objects.filter(
                        site=location_site).values_list(
                        'group__geocontext_group_key', flat=True)
                )
            except (ValueError, TypeError):
                pass
        for group_key in group_keys:
            if (all_context and
                    group_key in all_context):
                log('Context data already exists for {}'.format(
                    group_key
                ))
                continue
            current_outcome, message = (
                location_site.add_context_group(group_key))
            success = current_outcome
            log(str('[{status}] [{site_id}] [{group}] - {message}').format(
                status='SUCCESS' if success else 'FAILED',
                site_id=location_site.id,
                message=message,
                group=group_key
            ))

            if should_generate_site_code:
                site_code, catchments_data = generate_site_code(
                    location_site,
                    lat=location_site.latitude,
                    lon=location_site.longitude
                )
                location_site.site_code = site_code
                location_site.save()
                log(str('Site code {site_code} '
                    'generated for {site_id}').format(
                    site_code=site_code,
                    site_id=location_site.id
                ))


def merge_context_group(excluded_group=None, group_list=None):
    """
    Merge multiple location context groups
    """
    if not excluded_group:
        return
    if not group_list:
        return
    groups = group_list.exclude(id=excluded_group.id)

    if groups.count() < 1:
        return

    log('Merging %s data' % groups.count())

    links = [
        rel.get_accessor_name() for rel in excluded_group._meta.get_fields() if
        issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for group in groups:
            log('----- {} -----'.format(str(group)))
            for link in links:
                try:
                    objects = getattr(group, link).all()
                    if objects.count() > 0:
                        print('Updating {obj} for : {taxon}'.format(
                            obj=str(objects.model._meta.label),
                            taxon=str(group)
                        ))
                        update_dict = {
                            getattr(group, link).field.name: excluded_group
                        }
                        objects.update(**update_dict)
                except Exception as e:  # noqa
                    continue
            log(''.join(['-' for i in range(len(str(group)) + 12)]))

    groups.delete()
