import json
from typing import Dict

import requests
from bims.models.location_site import LocationSite
from requests.exceptions import HTTPError
from bims.location_site.river import fetch_river_name
from bims.utils.get_key import get_key

FBIS_CATCHMENT_KEY = 'river_catchment_areas_group'


def _fetch_catchments_data(catchment_key, lon, lat):
    """
    Fetch catchments data from geocontext
    :param catchment_key: catchment key in geocontext
    :param lon: longitude
    :param lon: latitude
    :return: list of catchment data, catchments object
    """
    catchments = {}
    catchment_data = {}
    catchment_url = (
        '{base_url}/api/v2/query?registry=group&key='
        '{catchment_key}&x={lon}&y={lat}'
    ).format(
        base_url=get_key('GEOCONTEXT_URL'),
        lon=lon,
        lat=lat,
        catchment_key=catchment_key
    )
    try:
        response = requests.get(catchment_url)
        if response.status_code == 200:
            catchment_data = json.loads(response.content)
            for _catchment in catchment_data['properties']['services']:
                catchments[_catchment['key']] = _catchment['value']
    except (HTTPError, ValueError, KeyError):
        pass
    return catchments, catchment_data


def _get_catchments_data(
        location_site=None, lat=None, lon=None, catchment_key='catchment'):
    """
    Get catchments data
    :return: list of catchment data
    """
    from bims.models.location_context import LocationContext

    catchment_key = catchment_key
    catchments = {}
    catchments_data = {}
    if not location_site:
        catchments, catchments_data = _fetch_catchments_data(
            catchment_key=catchment_key,
            lon=lon,
            lat=lat
        )
    if location_site:
        location_contexts = LocationContext.objects.filter(
            site=location_site
        )
        catchments = location_contexts.values_from_group(catchment_key)
        if not catchments:
            location_site.update_location_context_document(catchment_key)
            catchments = location_contexts.values_from_group(catchment_key)
    return catchments, catchments_data


def fbis_catchment_generator(
        location_site: LocationSite = None, lat=None, lon=None, river_name=''):
    """
    Generate catchment string for FBIS Site Code
    :param river_name: The name of the river
    :param location_site: Location site object
    :param lat: Latitude of site
    :param lon: Longitude of site
    :return: catchment string :
        2 characters from secondary catchment area
        4 characters from river name
        , catchments data in dictionary
    """
    catchment_code = ''
    catchments, catchments_data = _get_catchments_data(
        location_site=location_site,
        lat=lat,
        lon=lon,
        catchment_key=FBIS_CATCHMENT_KEY
    )
    for key, value in catchments.items():
        if 'secondary_catchment_area' in key and not catchment_code:
            catchment_code = value[:2].upper()
            break
    if location_site and not river_name:
        if location_site.legacy_river_name:
            river_name = location_site.legacy_river_name
        elif location_site.river:
            river_name = location_site.river.name
        else:
            river_name = fetch_river_name(
                location_site.geometry_point[1],
                location_site.geometry_point[0]
            )
    # Search river name by coordinates
    if not river_name and lat and lon:
        river_name = fetch_river_name(lat, lon)

    if river_name:
        river_name = river_name.replace(' ', '')
        catchment_code += river_name[:4].upper()
    return catchment_code, catchments_data


def rbis_catchment_generator(location_site=None, lat=None, lon=None):
    """
    Generate catchment string for RBIS Site Code
    :param location_site: Location site object
    :param lat: Latitude of site
    :param lon: Longitude of site
    :return: catchment string :
        1 character from catchment level_0 +
        2 characters from catchment level_1 +
        1 characters from catchment level_2
        , catchments data
    """
    catchment_key = 'rwanda_catchments'
    level_2 = ''
    district_id = ''
    catchments, catchments_data = _get_catchments_data(
        location_site=location_site,
        lat=lat,
        lon=lon,
        catchment_key=catchment_key
    )
    for key, value in catchments.items():
        if value:
            if 'level_2' in key and not level_2:
                level_2 = value[:6].upper()
                level_2 = level_2.replace('_', '')

    # Get district id
    geocontext_key = 'rwanda_district_id'
    district_data, district_geocontext_data = _get_catchments_data(
        location_site=location_site,
        lat=lat,
        lon=lon,
        catchment_key=geocontext_key
    )
    if district_data and 'districts_id' in district_data:
        district_id = district_data['districts_id']

    return level_2 + district_id, catchments_data


def wetland_catchment(lat, lon, wetland_data: Dict, user_wetland_name: str) -> str:
    """
    Generates a catchment code for a given wetland based on location and data.

    :param user_wetland_name: Wetland name from user
    :param lat: Latitude of the location site
    :param lon: Longitude of the location site
    :param wetland_data: A dictionary containing data about the wetland layer.
    :return: The generated catchment code, e.g. L112-NAME
    """
    from mobile.api_views.wetland import fetch_wetland_data

    wetland_site_code = ''
    quaternary_catchment_area_key = 'quaternary_catchment_area'
    catchments, catchments_data = _get_catchments_data(
        lat=lat,
        lon=lon,
        catchment_key=FBIS_CATCHMENT_KEY
    )
    if quaternary_catchment_area_key in catchments:
        wetland_site_code += catchments[quaternary_catchment_area_key]

    wetland_site_code += '-'
    if not wetland_data:
        wetland_data = fetch_wetland_data(
            float(lat),
            float(lon)
        )

    if wetland_data and 'name' in wetland_data and wetland_data['name']:
        wetland_site_code += wetland_data['name'][:4]
    elif user_wetland_name:
        wetland_site_code += user_wetland_name[:4]

    return wetland_site_code
