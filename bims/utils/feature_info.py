from typing import Union, Dict

import requests
from requests import HTTPError


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
