import logging
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from bims.models import LocationSite
from bims.models.water_temperature import calculate_indicators, \
    WaterTemperature, thermograph_data

logger = logging.getLogger('bims')


def get_all_days_of_year(year):
    from datetime import date, timedelta

    sdate = date(year, 1, 1)  # start date
    edate = date(year, 12, 31)  # end date

    delta = edate - sdate  # as timedelta
    days = []
    for i in range(delta.days + 1):
        day = sdate + timedelta(days=i)
        days.append(day)
    return days


class ThermalDataApiView(APIView):
    """Get thermal data"""

    def get(self, request, *args):
        site_id = request.GET.get('site-id', None)
        year = self.request.GET.get('year', None)
        start_date = self.request.GET.get('startDate', None)
        end_date = self.request.GET.get('endDate', None)
        indicator = {}
        thermograph = {}

        location_site = get_object_or_404(
            LocationSite,
            id=site_id
        )

        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            water_temperature = WaterTemperature.objects.filter(
                location_site=location_site,
                date_time__gte=start_date,
                date_time__lte=end_date
            )
            year = start_date.year
            if water_temperature:
                indicator = calculate_indicators(
                    location_site, year, True, water_temperature)
        else:
            if not year:
                years = list(WaterTemperature.objects.filter(
                    location_site=location_site
                ).values_list('date_time__year', flat=True).distinct(
                    'date_time__year').order_by('date_time__year'))
                year = years[-1]
            else:
                year = int(year.strip())
            indicator = calculate_indicators(
                location_site, year, True)
        if indicator and 'weekly' in indicator:
            thermograph = thermograph_data(indicator['weekly'])
            thermograph['date_time'] = indicator['date_time']
        return JsonResponse(
            thermograph
        )
