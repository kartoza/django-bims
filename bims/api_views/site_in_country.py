# coding=utf-8
import requests
import json

from geopy import Nominatim
from preferences import preferences
import logging

from bims.utils.get_key import get_key
from django.http import Http404
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response
from rest_framework.views import status

logger = logging.getLogger('bims')


class SiteInCountry(LoginRequiredMixin, APIView):
    """
    Check if site is inside base country
    """

    def get(self, request):
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)

        if not lat or not lon:
            raise Http404('Missing coordinates')
        boundary_key = preferences.SiteSetting.boundary_key

        if boundary_key:
            url = (
                '{base_url}/api/v2/query?registry=service&key={key}&'
                'x={lon}&y={lat}&outformat=json'
            ).format(
                base_url=get_key('GEOCONTEXT_URL'),
                key=boundary_key,
                lon=lon,
                lat=lat
            )
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    province = json.loads(response.content)
                    return Response(province['value'] is not None)

            except Exception as e:  # noqa
                pass

        base_country_code = preferences.SiteSetting.base_country_code
        if not base_country_code:
            return Response(True)
        geo_locator = Nominatim(user_agent='bims')

        try:
            location = geo_locator.reverse('{lat}, {lon}'.format(
                lat=lat,
                lon=lon
            ))
            base_country_codes = [
                country_code.lower() for country_code in
                preferences.SiteSetting.base_country_code.split(',')
            ]
            if (
                    location.raw['address']['country_code'] in
                    base_country_codes
            ):
                return Response(True)
        except Exception as e:  # noqa
            pass

        return Response({
            'data': 'Site is not in the country'},
            status=status.HTTP_404_NOT_FOUND)
