import json
import logging

import requests
from requests.exceptions import HTTPError
from bims.utils.get_key import get_key
from bims.models import LocationSite, LocationContext
from bims.utils.logger import log

logger = logging.getLogger('bims')


def fetch_river_name(latitude, longitude):
    """
    Fetch river name from GeoContext
    :param latitude: LocationSite latitude
    :param longitude: LocationSite longitude
    """
    river_name = ''
    base_geocontext_url = get_key('GEOCONTEXT_URL')
    api_url = '/api/v2/query?registry=service&key=river_name&'
    y = latitude
    x = longitude
    geocontext_url = '{base}{api_url}x={x}&y={y}&outformat=json'.format(
        base=base_geocontext_url,
        api_url=api_url,
        x=x,
        y=y
    )

    try:
        response = requests.get(geocontext_url)
        if response.status_code == 200:
            name = json.loads(response.content)
            river_name = name['value']
    except HTTPError:
        pass

    return river_name


def allocate_site_codes_from_river(update_site_code=True, location_id=None):
    """
    Allocate site codes to the existing location site
    :param update_site_code: should also update existing site codes
    :param location_id: location id to allocate site codes, if None, allocate
    all site
    """
    if location_id:
        location_sites = LocationSite.objects.filter(id=location_id)
    else:
        location_sites = LocationSite.objects.all()

    log('Allocating site code...')

    # Find location site that has river
    location_sites_with_river = location_sites.filter(
        river__isnull=False
    ).order_by('id')

    if not update_site_code:
        location_sites_with_river = location_sites_with_river.exclude(
            site_code__isnull=False
        )

    for location_site in location_sites_with_river:
        site_code = ''
        river_name = location_site.river.name
        # Get second catchment
        catchment_name = ''
        location_context = LocationContext.objects.filter(
            site=location_site
        )
        if location_context.exists():
            catchment_name = location_context.value_from_key(
                'secondary_catchment_area'
            )
        if len(catchment_name) > 0:
            catchment_name = catchment_name[:2].upper()
        site_code += catchment_name

        # Get first four letters of the river name
        river_name = river_name[:4].upper()
        if river_name:
            site_code += river_name
        else:
            continue

        # Add hyphen
        site_code += '-'
        # Add five letters describing location e.g. 00001
        existed_location_sites = LocationSite.objects.filter(
            site_code__contains=site_code
        ).exclude(id=location_site.id)

        site_code_number = len(existed_location_sites) + 1
        site_code_string = str(site_code_number).zfill(5)
        site_code += site_code_string

        # Check if location site already has site code with correct format
        if location_site.site_code[:4] == site_code[:4]:
            site_code_splitted = location_site.site_code.split('-')
            if len(site_code_splitted) > 1:
                old_site_code_number = site_code_splitted[1]
                if old_site_code_number == site_code_string:
                    log('Site code already exists')
                    continue

        if location_site.site_code and not location_site.legacy_site_code:
            location_site.legacy_site_code = location_site.site_code

        log('New Site Code : {}'.format(site_code))
        location_site.site_code = site_code
        location_site.save()
