
import time

from django.http import Http404
from django.views.generic import TemplateView
from django.db.models import Avg, F, Max, Min, Count
from django.db.models.aggregates import StdDev
from django.db.models.functions import TruncDay

from bims.models.location_site import LocationSite
from bims.models.water_temperature import WaterTemperature


THRESHOLD_VALUE = {
    'upper': {
        'maximum_threshold': 23.2,
        'minimum_threshold': 12.0,
        'mean_threshold': 18.0,
        'record_length': 0,
        'degree_days': 10.0
    },
    'lower': {
        'maximum_threshold': 23.2,
        'minimum_threshold': 12.0,
        'mean_threshold': 25.0,
        'record_length': 0,
        'degree_days': 10.0
    }
}


def get_thermal_zone(location_site: LocationSite):
    zone = (
        location_site.locationcontext_set.value_from_key(
            'thermal_zone').lower()
    )
    if not zone or zone == '-':
        zone = 'upper'
    else:
        if 'low' in zone:
            zone = 'lower'
        else:
            zone = 'upper'
    return zone


def calculate_indicators(location_site: LocationSite, year: int):

    month_name = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
        'Sep', 'Oct', 'Nov', 'Dec'
    ]

    indicators = dict()

    temperature_data_annual = WaterTemperature.objects.filter(
        location_site=location_site,
        date_time__year=year
    ).order_by('date_time')

    site_zone = get_thermal_zone(location_site)

    if not temperature_data_annual.exists():
        return indicators

    is_daily = temperature_data_annual.first().is_daily
    mean_key = 'value'
    max_key = 'maximum'
    min_key = 'minimum'

    if not is_daily:
        mean_key = 'mean'
        max_key = 'max'
        min_key = 'min'
        temperature_data_annual = temperature_data_annual.annotate(
            start_day=TruncDay('date_time')).values('start_day').order_by(
            'start_day').annotate(mean=Avg('value'), max=Max('value'),
                                  min=Min('value'),
                                  count=Count('id')).annotate(
            range=F('max') - F('min'))
    else:
        temperature_data_annual = temperature_data_annual.annotate(
            range=F('maximum') - F('minimum')
        )

    indicators['year'] = year
    indicators['monthly'] = {}
    indicators['annual'] = {}

    indicators['annual'] = temperature_data_annual.aggregate(
        annual_mean=Avg(mean_key),
        annual_max=Avg(max_key),
        annual_min=Avg(min_key),
        annual_range=Avg('range'),
        annual_sd=StdDev(mean_key),
        annual_range_sd=StdDev('range')
    )

    indicators['annual']['annual_cv'] = (
        (indicators['annual']['annual_sd'] * 100) /
        indicators['annual']['annual_mean']
    )

    for month in range(12):
        temperature_data_in_month = temperature_data_annual.filter(
            date_time__month=month+1
        )
        indicators['monthly'][month_name[month]] = (
            temperature_data_in_month.aggregate(
                monthly_mean=Avg(mean_key),
                monthly_max=Avg(max_key),
                monthly_min=Avg(min_key),
                monthly_range=Avg('range')
            )
        )

    if is_daily:
        temperature_data_annual = temperature_data_annual.values(
            'date_time', 'value', 'minimum', 'maximum'
        )

    weekly_data = {
        'weekly_mean_data': [],
        'weekly_min_data': [],
        'weekly_max_data': [],
    }
    thirty_data = {
        'thirty_min_data': [],
        'thirty_max_data': [],
    }
    ninety_data = {
        'ninety_min_data': [],
        'ninety_max_data': [],
    }

    weekly_mean_threshold = 0
    weekly_mean_threshold_dur = 0
    weekly_mean_threshold_dur_max = 0
    weekly_min_threshold = 0
    weekly_min_threshold_dur = 0
    weekly_min_threshold_dur_max = 0
    weekly_max_threshold = 0
    weekly_max_threshold_dur = 0
    weekly_max_threshold_dur_max = 0

    for day in range(6, len(temperature_data_annual)):
        mean_data = []
        min_data = []
        max_data = []

        min_data_30 = []
        max_data_30 = []

        min_data_90 = []
        max_data_90 = []

        for temp_data in temperature_data_annual[day - 6:day+1]:
            mean_data.append(temp_data[mean_key])
            min_data.append(temp_data[min_key])
            max_data.append(temp_data[max_key])

        if day >= 29:
            for temp_data in temperature_data_annual[day - 29:day+1]:
                min_data_30.append(temp_data[min_key])
                max_data_30.append(temp_data[max_key])

            thirty_data['thirty_min_data'].append(
                sum(min_data_30) / len(min_data_30))
            thirty_data['thirty_max_data'].append(
                sum(max_data_30) / len(max_data_30))

        if day >= 89:
            for temp_data in temperature_data_annual[day - 89:day+1]:
                min_data_90.append(temp_data[min_key])
                max_data_90.append(temp_data[max_key])

            ninety_data['ninety_min_data'].append(
                sum(min_data_90) / len(min_data_90))
            ninety_data['ninety_max_data'].append(
                sum(max_data_90) / len(max_data_90))

        weekly_mean_data = sum(mean_data) / len(mean_data)
        weekly_data['weekly_mean_data'].append(weekly_mean_data)
        # Check if weekly mean is exceeding the threshold
        if weekly_mean_data > THRESHOLD_VALUE[site_zone]['mean_threshold']:
            weekly_mean_threshold += 1
            weekly_mean_threshold_dur += 1
        else:
            if weekly_mean_threshold_dur > weekly_mean_threshold_dur_max:
                weekly_mean_threshold_dur_max = weekly_mean_threshold_dur
            weekly_mean_threshold_dur = 0

        weekly_min_data = sum(min_data) / len(min_data)
        weekly_data['weekly_min_data'].append(weekly_min_data)
        # Check if weekly min is exceeding the threshold
        if weekly_min_data > THRESHOLD_VALUE[site_zone]['minimum_threshold']:
            weekly_min_threshold += 1
            weekly_min_threshold_dur += 1
        else:
            if weekly_min_threshold_dur > weekly_min_threshold_dur_max:
                weekly_min_threshold_dur_max = weekly_min_threshold_dur
            weekly_min_threshold_dur = 0

        weekly_max_data = sum(max_data) / len(max_data)
        weekly_data['weekly_max_data'].append(weekly_max_data)
        # Check if weekly max is exceeding the threshold
        if weekly_max_data > THRESHOLD_VALUE[site_zone]['maximum_threshold']:
            weekly_max_threshold += 1
            weekly_max_threshold_dur += 1
        else:
            if weekly_max_threshold_dur > weekly_max_threshold_dur_max:
                weekly_max_threshold_dur_max = weekly_max_threshold_dur
            weekly_max_threshold_dur = 0

    indicators['weekly'] = {
        'weekly_mean_avg': (
            sum(weekly_data['weekly_mean_data']) /
            len(weekly_data['weekly_mean_data'])
        ),
        'weekly_min_avg': (
            sum(weekly_data['weekly_min_data']) /
            len(weekly_data['weekly_min_data'])
        ),
        'weekly_max_avg': (
            sum(weekly_data['weekly_max_data']) /
            len(weekly_data['weekly_max_data'])
        ),
    }

    indicators['thirty_days'] = {
        'thirty_max_avg': (
            sum(thirty_data['thirty_max_data']) /
            len(thirty_data['thirty_max_data'])
        ),
        'thirty_min_avg': (
            sum(thirty_data['thirty_min_data']) /
            len(thirty_data['thirty_min_data'])
        ),
    }

    indicators['ninety_days'] = {
        'ninety_max_avg': (
            sum(ninety_data['ninety_max_data']) /
            len(ninety_data['ninety_max_data'])
        ),
        'ninety_min_avg': (
            sum(ninety_data['ninety_min_data']) /
            len(ninety_data['ninety_min_data'])
        ),
    }

    if weekly_mean_threshold_dur > weekly_mean_threshold_dur_max:
        weekly_mean_threshold_dur_max = weekly_mean_threshold_dur
    if weekly_min_threshold_dur > weekly_min_threshold_dur_max:
        weekly_min_threshold_dur_max = weekly_min_threshold_dur
    if weekly_max_threshold_dur > weekly_max_threshold_dur_max:
        weekly_max_threshold_dur_max = weekly_max_threshold_dur

    indicators['threshold'] = {
        'weekly_mean': weekly_mean_threshold,
        'weekly_min': weekly_min_threshold,
        'weekly_max': weekly_max_threshold,
        'weekly_mean_dur': weekly_mean_threshold_dur_max,
        'weekly_min_dur': weekly_min_threshold_dur_max,
        'weekly_max_dur': weekly_max_threshold_dur_max,
    }

    return indicators


class ThermalDashboardView(TemplateView):
    template_name = 'thermal/indicators_of_thermal_alteration.html'

    def get_context_data(self, **kwargs):
        start_time = time.time()
        context = (
            super(ThermalDashboardView, self).get_context_data(**kwargs)
        )

        site_id = self.request.GET.get('site-id', None)
        year = self.request.GET.get('year', None)

        if not site_id:
            raise Http404()

        location_site = LocationSite.objects.get(id=site_id)
        context['years'] = list(WaterTemperature.objects.filter(
            location_site=location_site
        ).values_list('date_time__year', flat=True).distinct(
            'date_time__year').order_by('date_time__year'))

        if not year:
            year = context['years'][-1]
        else:
            year = int(year.strip())

        context['location_site'] = location_site
        context['indicators'] = calculate_indicators(location_site, year)
        context['execution_time'] = time.time() - start_time

        return context
