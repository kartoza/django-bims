from preferences import preferences

from bims.models.location_context import LocationContext
from bims.models.location_site import LocationSite
from bims.utils.site_code import get_feature_data


def get_geomorphological_zone_class(location_site: LocationSite) -> str:
    """
    Get geomorphological zone class from the location site,
        if it has the required data
    :param location_site: Location site object
    :return: Upper, Lower, or empty string
    """

    upper_data = [
        'mountain headwater stream',
        'mountain stream',
        'transitional',
        'upper foothill'
    ]
    lower_data = [
        'lower foothill',
        'lowland river'
    ]

    if location_site.refined_geomorphological:
        if location_site.refined_geomorphological.lower() in upper_data:
            return 'Upper'
        elif location_site.refined_geomorphological.lower() in lower_data:
            return 'Lower'

    context = LocationContext.objects.filter(
        site=location_site
    )
    geo_class = context.value_from_key(
        layer_name='geomorphological zone'
    )
    if geo_class == '-':
        geo_class = get_feature_data(
            lon=location_site.longitude,
            lat=location_site.latitude,
            context_key='name',
            layer_name='geomorphological',
            tolerance=preferences.GeocontextSetting.tolerance,
            location_site=location_site,
        )

    if geo_class != '-' or not geo_class:
        if geo_class:
            if geo_class.lower().strip() in upper_data:
                return 'Upper'
            elif geo_class.lower().strip() in lower_data:
                return 'Lower'

    geo_class_recoded = context.value_from_key(
        'geo_class_recoded'
    )
    if geo_class_recoded:
        if geo_class_recoded.lower().strip() in upper_data:
            return 'Upper'
        elif geo_class_recoded.lower().strip() in lower_data:
            return 'Lower'

    return ''
