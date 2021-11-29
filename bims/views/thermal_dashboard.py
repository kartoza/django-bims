
import time

from django.http import Http404
from django.views.generic import TemplateView
from django.db.models import Avg, F, RowRange, Window
from django.db.models.aggregates import StdDev

from bims.models.location_site import LocationSite
from bims.models.water_temperature import WaterTemperature


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

    if not temperature_data_annual.exists():
        return indicators

    temperature_data_annual = temperature_data_annual.annotate(
        range=F('maximum') - F('minimum')
    )

    indicators['year'] = year
    indicators['monthly'] = {}
    indicators['annual'] = {}

    indicators['annual'] = temperature_data_annual.aggregate(
        annual_mean=Avg('value'),
        annual_max=Avg('maximum'),
        annual_min=Avg('minimum'),
        annual_range=Avg('range'),
        annual_sd=StdDev('value'),
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
                monthly_mean=Avg('value'),
                monthly_max=Avg('maximum'),
                monthly_min=Avg('minimum'),
                monthly_range=Avg('range')
            )
        )

    weekly_data = temperature_data_annual.annotate(
        weekly_mean=Window(
            expression=Avg('value'),
            order_by=F('date_time').asc(),
            frame=RowRange(start=-6, end=0)
        ),
        weekly_min=Window(
            expression=Avg('minimum'),
            order_by=F('date_time').asc(),
            frame=RowRange(start=-6, end=0)
        ),
        weekly_max=Window(
            expression=Avg('maximum'),
            order_by=F('date_time').asc(),
            frame=RowRange(start=-6, end=0)
        )
    )

    weekly_data_filtered = weekly_data[6:]

    indicators['weekly'] = weekly_data_filtered.aggregate(
        weekly_mean_avg=Avg('weekly_mean'),
        weekly_min_avg=Avg('weekly_min'),
        weekly_max_avg=Avg('weekly_max')
    )

    thirty_days_data = temperature_data_annual.annotate(
        thirty_min=Window(
            expression=Avg('minimum'),
            order_by=F('date_time').asc(),
            frame=RowRange(start=-29, end=0)
        ),
        thirty_max=Window(
            expression=Avg('maximum'),
            order_by=F('date_time').asc(),
            frame=RowRange(start=-29, end=0)
        ),
    )

    thirty_days_data_filtered = thirty_days_data[29:]
    indicators['thirty_days'] = thirty_days_data_filtered.aggregate(
        thirty_max_avg=Avg('thirty_max'),
        thirty_min_avg=Avg('thirty_min')
    )

    ninety_days_data = temperature_data_annual.annotate(
        ninety_min=Window(
            expression=Avg('minimum'),
            order_by=F('date_time').asc(),
            frame=RowRange(start=-89, end=0)
        ),
        ninety_max=Window(
            expression=Avg('maximum'),
            order_by=F('date_time').asc(),
            frame=RowRange(start=-89, end=0)
        ),
    )

    ninety_days_data_filtered = ninety_days_data[89:]
    indicators['ninety_days'] = ninety_days_data_filtered.aggregate(
        ninety_max_avg=Avg('ninety_max'),
        ninety_min_avg=Avg('ninety_min')
    )

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
