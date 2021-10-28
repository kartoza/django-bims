import codecs
import csv
from datetime import datetime
from braces.views import LoginRequiredMixin
from django.utils.timezone import make_aware
from django.views import View
from bims.models.basemap_layer import BaseMapLayer
import logging
from bims.utils.get_key import get_key
from django.http import HttpResponseForbidden
from bims.models.location_site import LocationSite
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from bims.models import WaterTemperature, UploadSession
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from bims.views.mixin.session_form.mixin import SessionFormMixin
from django.shortcuts import get_object_or_404
from django.http import Http404

logger = logging.getLogger('bims')

LOGGING_INTERVAL = [0.5, 1, 2, 3, 24]
RECORDS_PER_INTERVAL = {
    '0.5': 48,
    '1': 24,
    '2': 12,
    '3': 8
}
CATEGORY = 'water_temperature'


class WaterTemperatureView(TemplateView, SessionFormMixin):
    """View for water temperature form"""
    template_name = 'water_temperature_form.html'

    def get_context_data(self, **kwargs):

        context = super(WaterTemperatureView, self).get_context_data(**kwargs)
        if not self.location_site:
            return context
        context['geoserver_public_location'] = get_key(
            'GEOSERVER_PUBLIC_LOCATION')
        context['location_site_name'] = self.location_site.name
        context['location_site_code'] = self.location_site.site_code
        context['location_site_lat'] = self.location_site.get_centroid().y
        context['location_site_long'] = self.location_site.get_centroid().x
        context['site_id'] = self.location_site.id
        context['logging_interval'] = LOGGING_INTERVAL

        try:
            context['bing_key'] = BaseMapLayer.objects.get(source_type='bing').key
        except BaseMapLayer.DoesNotExist:
            context['bing_key'] = ''

        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        site_id = request.GET.get('siteId', None)
        if site_id:
            self.location_site = get_object_or_404(
                LocationSite,
                pk=site_id
            )
        else:
            raise Http404()

        return super(WaterTemperatureView, self).get(request, *args, **kwargs)


class WaterTemperatureValidateView(View, LoginRequiredMixin):

    is_valid = True
    error_messages = []

    def add_error_messages(self, row, message):
        self.is_valid = False
        self.error_messages.append(
            f'{row} : {message}'
        )

    def post(self, request, *args, **kwargs):
        self.error_messages = []
        self.is_valid = True
        is_daily = False
        finished = False
        times = []

        water_file = request.FILES.get('water_file')

        date_format = request.POST.get('format')
        interval = request.POST.get('interval')

        if float(interval) != 24:
            date_format = date_format + ' %H:%M'
        else:
            is_daily = True

        row = 2
        reader = csv.DictReader(codecs.iterdecode(water_file, 'utf-8'))
        headers = reader.fieldnames
        data = list(reader)
        date_field = 'Date Time' if 'Date Time' in headers else 'Date'

        if is_daily:
            if not any(header in ['Mean', 'Minimum', 'Maximum'] for header in
                   headers):
                self.add_error_messages(
                    row,
                    'Missing minimum and maximum data value'
                )
                finished = True

        if not finished:
            for temperature_data in data:
                # Check date format
                try:
                    date = datetime.strptime(
                        temperature_data[date_field], date_format)
                    # Check interval
                    if not is_daily:
                        if len(times) == 0 and date.hour != 0:
                            self.add_error_messages(
                                row,
                                'Non daily data should start at 00'
                            )
                        if date.hour == 0 and len(times) > 1:
                            if times[len(times)-1].hour != 23:
                                self.add_error_messages(
                                    row-1,
                                    'Non daily data should end at 23'
                                )
                            if len(times) < RECORDS_PER_INTERVAL[interval]:
                                self.add_error_messages(
                                    row-1,
                                    'Data for this day is not complete'
                                )
                            times = []
                        times.append(date)
                except ValueError:
                    self.add_error_messages(
                        row,
                        'Date format should be {}'.format(
                            date_format
                        )
                    )

                row += 1

        if not self.is_valid:
            return JsonResponse({
                'status': 'failed',
                'message': self.error_messages
            })
        else:
            upload_session = UploadSession.objects.create(
                uploader=request.user,
                process_file=water_file,
                uploaded_at=datetime.now(),
                category=CATEGORY
            )
            return JsonResponse({
                'status': 'success',
                'message': 'Water temperature is validated',
                'upload_session_id': upload_session.id
            })


class WaterTemperatureUploadView(View, LoginRequiredMixin):
    location_site = None
    upload_task = None

    def post(self, request, *args, **kwargs):

        if not request.is_ajax():
            return HttpResponseForbidden()
        owner_id = request.POST.get('owner_id', '').strip()
        interval = request.POST.get('interval')
        date_format = request.POST.get('format')
        upload_session_id = request.POST.get('upload_session_id')
        location_site = LocationSite.objects.get(
            pk=request.POST.get('site-id', None)
        )
        is_daily = False

        if float(interval) != 24:
            date_format = date_format + ' %H:%M'
        else:
            is_daily = True

        try:
            upload_session = UploadSession.objects.get(
                id=upload_session_id
            )
        except UploadSession.DoesNotExist:
            raise Http404('Upload session not found')

        with open(upload_session.process_file.path) as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames
            data = list(reader)
            date_field = 'Date Time' if 'Date Time' in headers else 'Date'

            for temperature in data:

                if is_daily:
                    water_temp_value = temperature['Mean']
                else:
                    water_temp_value = temperature['Water temperature']

                water_temp, created = WaterTemperature.objects.get_or_create(
                    date_time=make_aware(
                        datetime.strptime(
                            temperature[date_field],
                            date_format)
                    ),
                    location_site=location_site,
                    is_daily=is_daily,
                    defaults={
                        'value': water_temp_value
                    }
                )
                if is_daily:
                    water_temp.value = water_temp_value
                    water_temp.minimum = temperature['Minimum']
                    water_temp.maximum = temperature['Maximum']
                else:
                    water_temp.value = water_temp_value

                water_temp.source_file = upload_session.process_file.path
                water_temp.uploader = self.request.user
                water_temp.owner = get_user_model().objects.get(
                    id=int(owner_id))
                water_temp.save()

            upload_session.processed = True
            upload_session.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Water temperature date being uploaded. Thank you'
            })
