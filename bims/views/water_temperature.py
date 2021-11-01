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

        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

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
                        time_string = date.strftime('%H:%M')
                        if len(times) == 0 and time_string != start_time:
                            self.add_error_messages(
                                row,
                                'Non daily data should start at {}'.format(
                                    start_time
                                )
                            )
                        if time_string == start_time and len(times) > 1:
                            if (
                                times[len(times)-1].strftime(
                                    '%H:%M'
                                ) != end_time
                            ):
                                self.add_error_messages(
                                    row-1,
                                    'Non daily data should end at {}'.format(
                                        end_time
                                    )
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
        new_data = []
        existing_data = []

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

                date_time = make_aware(
                    datetime.strptime(
                        temperature[date_field],
                        date_format)
                )

                water_data = {
                    'date_time': date_time,
                    'location_site': location_site,
                    'is_daily': is_daily
                }

                query = WaterTemperature.objects.filter(
                    **water_data
                )
                is_data_exists = query.exists()
                water_data['value'] = water_temp_value
                water_data['minimum'] = temperature['Minimum'] if is_daily else 0
                water_data['maximum'] = temperature['Maximum'] if is_daily else 0

                if is_data_exists:
                    new_query = query.filter(**water_data)
                    if not new_query.exists():
                        existing_water_data = query.first()
                        existing_water_data.value = water_temp_value
                        existing_water_data.minimum = water_data['minimum']
                        existing_water_data.maximum = water_data['maximum']
                        existing_data.append(existing_water_data)
                else:
                    new_data.append(
                        WaterTemperature(**water_data)
                    )

            success_response = ''
            if new_data:
                WaterTemperature.objects.bulk_create(
                    new_data
                )
                success_response = '{} data has been added. '.format(
                    len(new_data)
                )
            if existing_data:
                WaterTemperature.objects.bulk_update(
                    existing_data,
                    ['value', 'minimum', 'maximum']
                )
                success_response += '{} data has been updated.'.format(
                    len(existing_data)
                )

            if not success_response:
                success_response = 'No new data added or updated.'

            upload_session.processed = True
            upload_session.save()

            return JsonResponse({
                'status': 'success',
                'message': success_response
            })
