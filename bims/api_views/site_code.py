# coding=utf-8
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response

from bims.models.location_site import LocationSite, generate_site_code


class GetSiteCode(LoginRequiredMixin, APIView):

    def get(self, request):
        from bims.location_site.river import fetch_river_name

        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)
        site_id = request.GET.get('site_id', None)
        river_name = request.GET.get(
            'user_river_name', ''
        )
        location_site = None
        if site_id:
            try:
                location_site = LocationSite.objects.get(
                    id=site_id
                )
            except LocationSite.DoesNotExist:
                pass

        if not river_name:
            river_name = fetch_river_name(lat, lon)

        site_code, catchment = generate_site_code(
            location_site=location_site,
            lat=lat,
            lon=lon,
            river_name=river_name
        )

        return Response({
            'river': river_name,
            'catchment': catchment,
            'site_code': site_code
        })
