
import time

from django.http import Http404
from django.views.generic import TemplateView

from bims.models.location_site import LocationSite
from bims.models.water_temperature import WaterTemperature, \
    calculate_indicators


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
