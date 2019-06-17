# coding=utf-8
import json
import requests
from requests.exceptions import HTTPError
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response

from bims.location_site.river import fetch_river_name
from bims.utils.get_key import get_key
from bims.location_site.river import generate_site_code
from bims.models.location_site import LocationSite


class GetSiteCode(LoginRequiredMixin, APIView):

    def get(self, request):
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)
        site_id = request.GET.get('site_id', None)
        location_site = None
        if site_id:
            try:
                location_site = LocationSite.objects.get(
                    id=site_id
                )
            except LocationSite.DoesNotExist:
                pass

        catchment = ''
        secondary_catchment_area = ''

        river_name = fetch_river_name(lat, lon)

        catchment_url = (
            '{base_url}/api/v1/geocontext/value/group/'
            '{lon}/{lat}/river_catchment_areas_group/'
        ).format(
            base_url=get_key('GEOCONTEXT_URL'),
            lon=lon,
            lat=lat
        )

        try:
            response = requests.get(catchment_url)
            if response.status_code == 200:
                catchment = json.loads(response.content)
                secondary_catchment_area = (
                    catchment['service_registry_values'][1][
                        'value']
                )
        except (HTTPError, ValueError, KeyError):
            pass

        return Response({
            'river': river_name,
            'catchment': catchment,
            'site_code': generate_site_code(
                river_name=river_name,
                catchment=secondary_catchment_area,
                location_site=location_site
            )
        })
