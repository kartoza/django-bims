from bims.models.location_context import LocationContext
from bims.models.location_site import LocationSite


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
        'geo_class'
    )
    if geo_class != '-':
        return geo_class

    geo_class_recoded = context.value_from_key(
        'geo_class_recoded'
    )
    if geo_class_recoded:
        if geo_class_recoded.lower().strip() in upper_data:
            return 'Upper'
        elif geo_class_recoded.lower().strip() in lower_data:
            return 'Lower'

    return ''
