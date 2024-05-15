from typing import Union, Dict

import requests
from requests import HTTPError
from django.contrib.gis.geos import GEOSGeometry


def get_feature_info_from_wms(
        base_wms_url: str,
        layer: str, srs: str,
        latitude: float,
        longitude: float, width: int, height: int) -> Union[Dict, None]:
    """
    Fetch feature information from a WMS layer based on given latitude and longitude.

    Parameters:
        base_wms_url (str): The base URL of the WMS service.
        layer (str): The name of the WMS layer to query.
        srs (str): The Spatial Reference System (e.g., "EPSG:4326").
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.
        width (int): The width of the map in pixels.
        height (int): The height of the map in pixels.

    Returns:
        Union[Dict, None]: Returns a dictionary containing the feature info if successful, or None if unsuccessful.

    Examples:
        >>> get_feature_info_from_wms("http://your.wms.server", "your_layer", "EPSG:4326", 40.7128, -74.0060, 800, 600)
        {...}  # Feature information in dictionary form
    """

    params = {
        'request': 'GetFeatureInfo',
        'service': 'WMS',
        'srs': srs,
        'version': '1.1.1',
        'format': 'image/png',
        'layers': layer,
        'query_layers': layer,
        'info_format': 'application/json',
        'width': width,
        'height': height,
        'x': int(width / 2),
        'y': int(height / 2),
        'bbox': f"{longitude-0.1},{latitude-0.1},{longitude+0.1},{latitude+0.1}"
    }

    try:
        response = requests.get(base_wms_url, params=params)
        if response.status_code == 200:
            return response.json()
    except HTTPError:
        return None

    return None


def get_feature_centroid(lat, lon, wfs_url, layer_name):
    """
    Get the centroid of a WFS layer feature intersecting with the given lat/lon coordinates using Django GIS.

    :param lat: Latitude of the point.
    :param lon: Longitude of the point.
    :param wfs_url: URL of the WFS service.
    :param layer_name: Name of the layer to query.
    :return: A tuple containing the centroid's latitude and longitude or None if no feature is found.
    """
    # Construct WFS request with spatial filter (CQL_FILTER) for GeoJSON format
    params = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typeName': layer_name,
        'outputFormat': 'application/json',
        'srsName': 'EPSG:4326',
        'CQL_FILTER': f"INTERSECTS(geom, POINT({lon} {lat}))"
    }

    try:
        response = requests.get(wfs_url, params=params)
        response.raise_for_status()
        features = response.json().get('features')
        if features:
            geometry = GEOSGeometry(str(features[0]['geometry']))
            centroid = geometry.centroid
            return centroid.y, centroid.x
        else:
            print("No feature found at the provided coordinates.")
            return None
    except requests.RequestException as e:
        print(f"Error fetching the WFS data: {e}")
        return None
