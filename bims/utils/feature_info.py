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


def get_feature_centroid(wfs_url, layer_name, attribute_key=None, attribute_value=None, lat=None, lon=None):
    """
    Get the centroid of a WFS layer feature intersecting with the given attribute key/value or lat/lon

    :param wfs_url: URL of the WFS service.
    :param layer_name: Name of the layer to query.
    :param attribute_key: Attribute key to filter the feature.
    :param attribute_value: Attribute value to filter the feature.
    :param lat: Latitude of the point (optional if attribute_key and attribute_value are provided).
    :param lon: Longitude of the point (optional if attribute_key and attribute_value are provided).
    :return: A tuple containing the centroid's latitude and longitude or None if no feature is found.
    """
    if (lat is None or lon is None) and (attribute_key is None or attribute_value is None):
        raise ValueError("Either lat/lon or attribute_key/attribute_value must be provided.")

    # Construct CQL_FILTER based on provided parameters
    if attribute_key and attribute_value:
        cql_filter = f"{attribute_key} = '{attribute_value}'"
    else:
        cql_filter = f"INTERSECTS(geom, POINT({lon} {lat}))"

    # Construct WFS request with the CQL_FILTER for GeoJSON format
    params = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typeName': layer_name,
        'outputFormat': 'application/json',
        'srsName': 'EPSG:4326',
        'CQL_FILTER': cql_filter
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
            print("No feature found with the provided parameters.")
            return None
    except requests.RequestException as e:
        print(f"Error fetching the WFS data: {e}")
        return None
