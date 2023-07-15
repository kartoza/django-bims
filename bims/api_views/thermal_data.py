import ast
import logging
from datetime import datetime

from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from bims.models import LocationSite
from bims.models.water_temperature import calculate_indicators, \
    WaterTemperature, thermograph_data, WaterTemperatureThreshold, get_thermal_zone

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


class WaterTemperatureThresholdApiView(APIView):

    def get(self, request, *args):
        location_site = LocationSite.objects.get(
            id=request.GET.get('location_site', None)
        )
        threshold = WaterTemperatureThreshold.objects.filter(
            location_site=location_site
        ).first()
        if not threshold:
            WaterTemperatureThreshold.objects.first()
        thermal_zone = get_thermal_zone(location_site)

        return JsonResponse({
            'maximum_threshold': (
                threshold.upper_maximum_threshold if thermal_zone == 'upper' else threshold.lower_maximum_threshold
            ),
            'minimum_threshold': (
                threshold.upper_minimum_threshold if thermal_zone == 'upper' else threshold.lower_minimum_threshold
            ),
            'mean_threshold': (
                threshold.upper_mean_threshold if thermal_zone == 'upper' else threshold.lower_mean_threshold
            ),
            'record_length': (
                threshold.upper_record_length if thermal_zone == 'upper' else threshold.lower_record_length
            ),
            'degree_days': (
                threshold.upper_degree_days if thermal_zone == 'upper' else threshold.lower_degree_days
            )
        })

    def post(self, request, *args):
        if not request.user.is_authenticated:
            raise Http404()

        try:
            location_site = LocationSite.objects.get(
                id=request.GET.get('location_site', None)
            )
            water_temperature_id = request.GET.get(
                'water_temperature'
            )
            is_owner = (
                WaterTemperature.objects.get(
                    id=water_temperature_id
                ).owner == request.user
            )

            if not is_owner and not request.user.is_superuser:
                raise Exception()

            thermal_zone = get_thermal_zone(location_site)

            threshold = WaterTemperatureThreshold.objects.filter(
                location_site=location_site
            ).first()

            if not threshold:
                threshold = WaterTemperatureThreshold.objects.create(
                    location_site=location_site
                )
            if not threshold:
                return JsonResponse(
                    {'error': 'No WaterTemperatureThreshold found.'},
                    status=status.HTTP_404_NOT_FOUND)

            if thermal_zone == 'upper':
                threshold.upper_maximum_threshold = request.data.get(
                    'maximum_threshold', threshold.upper_maximum_threshold)
                threshold.upper_minimum_threshold = request.data.get(
                    'minimum_threshold', threshold.upper_minimum_threshold)
                threshold.upper_mean_threshold = request.data.get(
                    'mean_threshold', threshold.upper_mean_threshold)
                threshold.upper_record_length = request.data.get(
                    'record_length', threshold.upper_record_length)
                threshold.upper_degree_days = request.data.get(
                    'degree_days', threshold.upper_degree_days)
            else:
                threshold.lower_maximum_threshold = request.data.get(
                    'maximum_threshold', threshold.lower_maximum_threshold)
                threshold.lower_minimum_threshold = request.data.get(
                    'minimum_threshold', threshold.lower_minimum_threshold)
                threshold.lower_mean_threshold = request.data.get(
                    'mean_threshold', threshold.lower_mean_threshold)
                threshold.lower_record_length = request.data.get(
                    'record_length', threshold.lower_record_length)
                threshold.lower_degree_days = request.data.get(
                    'degree_days', threshold.lower_degree_days)

            threshold.save()
            return HttpResponse('Threshold updated successfully.', status=status.HTTP_200_OK)
        except Exception as e:
            return HttpResponse('An error occurred: ' + str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
