from typing import Union, Dict

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from bims.utils.feature_info import get_feature_info_from_wms


def fetch_wetland_data(latitude: float, longitude: float) -> Union[Dict, None]:
    """
    Fetch wetland data from GeoContext based on given latitude and longitude.

    Parameters:
        latitude (float): The latitude of the LocationSite.
        longitude (float): The longitude of the LocationSite.

    Returns:
        Union[Dict, None]: Returns a dictionary containing the wetland data if the fetch is successful.
                           Returns None if the fetch fails.

    Examples:
        >>> fetch_wetland_data(40.7128, -74.0060)
        {...}  # some wetland data in dictionary form

        >>> fetch_wetland_data(0, 0)
        None
    """
    wetland = None
    wetland_layer_name = 'kartoza:nwm6_beta_v3_20230714'
    base_wms_layer = 'https://maps.kartoza.com/geoserver/wms'

    wms_data = get_feature_info_from_wms(
        base_wms_layer,
        wetland_layer_name,
        'EPSG:4326',
        latitude,
        longitude,
        800, 600
    )

    if wms_data and 'features' in wms_data and wms_data['features']:
        feature_data = wms_data['features'][0]
        wetland = feature_data['properties']

    return wetland


class FetchWetland(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args):
        lat = float(request.GET.get('lat', '0'))
        lon = float(request.GET.get('lon', '0'))

        wetland = fetch_wetland_data(
            lat,
            lon
        )

        return Response(wetland)
