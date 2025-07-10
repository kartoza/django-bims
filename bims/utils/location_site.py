from collections import OrderedDict

from preferences import preferences

from bims.enums.ecosystem_type import ECOSYSTEM_WETLAND
from bims.models import (
    LocationContextFilterGroupOrder,
    LocationSite,
    LocationContext
)


def overview_site_detail(site_id: int):
    def parse_string(string_in):
        if not string_in:
            return '-'
        else:
            if isinstance(string_in, str):
                return string_in.strip()
            return str(string_in)
    try:
        location_site = LocationSite.objects.get(id=site_id)
    except LocationSite.DoesNotExist:
        return {}
    location_context = LocationContext.objects.filter(site=location_site)
    site_river = '-'
    if location_site.river:
        site_river = location_site.river.name
    overview = dict()
    overview['{} Site Code'.format(
        preferences.SiteSetting.default_site_name
    )] = location_site.site_code
    overview['User Site Code'] = location_site.legacy_site_code
    overview['Site coordinates'] = (
        'Longitude: {long}, Latitude: {lat}'.format(
            long=parse_string(location_site.longitude),
            lat=parse_string(location_site.latitude)
        )
    )
    if location_site.site_description:
        overview['Site description'] = parse_string(
            location_site.site_description
        )
    else:
        overview['Site description'] = parse_string(
            location_site.name
        )

    result = dict()
    result['Site details'] = overview

    if preferences.SiteSetting.site_code_generator == 'fbis':
        river_and_geo = OrderedDict()
        river_and_geo['Ecosystem Type'] = (
            location_site.ecosystem_type if location_site.ecosystem_type else 'Unspecified'
        )
        river_and_geo['River'] = site_river
        river_and_geo[
            'User River Name'] = (
            location_site.legacy_river_name if location_site.legacy_river_name else '-'
        )
        river_and_geo['Geomorphological zone'] = (
            location_context.value_from_key(
                layer_name='Geomorphological Zone')
        )
        refined_geomorphological = '-'
        if location_site.refined_geomorphological:
            refined_geomorphological = (
                location_site.refined_geomorphological
            )
        river_and_geo['User Geomorphological zone'] = (
            refined_geomorphological
        )
        river_and_geo['Wetland Name (NWM6)'] = (
            location_site.wetland_name if location_site.wetland_name else '-'
        )
        river_and_geo['User Wetland Name'] = (
            location_site.user_wetland_name if location_site.user_wetland_name else '-'
        )
        river_and_geo['Hydrogeomorphic Type (NWM6)'] = (
            location_site.hydrogeomorphic_type if location_site.hydrogeomorphic_type else '-'
        )
        river_and_geo['User Hydrogeomorphic Type'] = (
            location_site.user_hydrogeomorphic_type if location_site.user_hydrogeomorphic_type else '-'
        )

        wetland_area = ''
        if location_site.ecosystem_type == ECOSYSTEM_WETLAND and location_site.additional_data:
            wetland_area = location_site.additional_data.get('area_ha', '')

        river_and_geo['Wetland area (hectares)'] = (
            wetland_area if wetland_area else '-'
        )

        result['Ecosystem Characteristics'] = river_and_geo

    # Location context group data
    location_context_filters = (
        LocationContextFilterGroupOrder.objects.filter(
            show_in_dashboard=True
        ).order_by('group_display_order')
    )

    for context_filter in location_context_filters:
        title = context_filter.filter.title
        if title not in result:
            result[title] = {}
        result[title][context_filter.group.name] = (
            location_context.value_from_key(
                context_filter.group.key
            )
        )

    return result
