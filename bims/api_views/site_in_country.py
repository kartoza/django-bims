# coding=utf-8
import requests
from django.http import Http404
from geopy.geocoders import Nominatim
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response
from rest_framework import status
from preferences import preferences


class SiteInCountry(LoginRequiredMixin, APIView):
    """
    Check if site is inside base country
    """
    def get(self, request):
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)
        if not lat or not lon:
            raise Http404('Missing coordinates')
        base_country_code = preferences.SiteSetting.base_country_code
        if not base_country_code:
            return Response(True)

        geo_locator = Nominatim(user_agent='bims')
        location = geo_locator.reverse('{lat}, {lon}'.format(
            lat=lat,
            lon=lon
        ))
        base_country_code = preferences.SiteSetting.base_country_code
        if (
            location.raw['address']['country_code'] ==
            base_country_code.lower()
        ):
            return Response(True)

        return Response({
            'data': 'Site is not in the country'},
            status=status.HTTP_404_NOT_FOUND)
