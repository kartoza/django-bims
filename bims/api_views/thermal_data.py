import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from bims.models import LocationSite
from bims.models.water_temperature import calculate_indicators, \
    WaterTemperature, thermograph_data

logger = logging.getLogger('bims')


class ThermalDataApiView(APIView):
    """Get thermal data"""

    def get(self, request, *args):
        site_id = request.GET.get('site-id', None)
        year = self.request.GET.get('year', None)

        location_site = get_object_or_404(
            LocationSite,
            id=site_id
        )

        if not year:
            years = list(WaterTemperature.objects.filter(
                location_site=location_site
            ).values_list('date_time__year', flat=True).distinct(
                'date_time__year').order_by('date_time__year'))
            year = years[-1]
        else:
            year = int(year.strip())

        indicator = calculate_indicators(location_site, year, True)
        thermograph = {}
        if 'weekly' in indicator:
            thermograph = thermograph_data(indicator['weekly'])

        return JsonResponse(thermograph)
