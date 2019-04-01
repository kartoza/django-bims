import requests
from requests.exceptions import HTTPError
from bims.utils.get_key import get_key


def fetch_river_name(location_site):
    """
    Fetch river name from GeoContext
    :param location_site: LocationSite object
    """
    name = ''
    base_geocontext_url = get_key('GEOCONTEXT_URL')
    api_url = '/api/v1/geocontext/river-name/'
    y = location_site.latitude
    x = location_site.longitude
    geocontext_url = '{base}{api_url}{x}/{y}/'.format(
        base=base_geocontext_url,
        api_url=api_url,
        x=x,
        y=y
    )

    try:
        response = requests.get(geocontext_url)
        if response.status_code == 200:
            name = response.content
            name = name.strip('\"')
    except HTTPError:
        pass

    return name
