import codecs
import csv
import json
import time
from datetime import datetime
from braces.views import LoginRequiredMixin
from django.utils.timezone import make_aware
from django.contrib.auth import get_user_model
from django.views import View
import logging
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.http import Http404

from bims.models.basemap_layer import BaseMapLayer
from bims.utils.get_key import get_key
from bims.models.location_site import LocationSite
from bims.models import (
    WaterTemperature,
    UploadSession,
    calculate_indicators,
    SourceReference,
    SiteImage, WATER_TEMPERATURE_KEY
)

from bims.views.mixin.session_form import SessionFormMixin

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
    additional_context = {}

    def get_context_data(self, **kwargs):

        context = super(
            WaterTemperatureView, self).get_context_data(**kwargs)
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
            context['bing_key'] = BaseMapLayer.objects.get(
                source_type='bing').key
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
        else:
            if 'Water temperature' not in headers:
                self.add_error_messages(
                    row,
                    'Missing "Water temperature" header'
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
                                    times[len(times) - 1].strftime(
                                        '%H:%M'
                                    ) != end_time
                            ):
                                self.add_error_messages(
                                    row - 1,
                                    'Non daily data should end at {}'.format(
                                        end_time
                                    )
                                )
                            if len(times) < RECORDS_PER_INTERVAL[interval]:
                                self.add_error_messages(
                                    row - 1,
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
        source_reference_id = request.POST.get('source_reference', '')
        site_image_file = request.FILES.get('site_image')

        source_reference = None
        location_site = LocationSite.objects.get(
            pk=request.POST.get('site-id', None)
        )

        site_image = None
        success_response_image = ''
        if site_image_file:
            site_image = SiteImage.objects.get_or_create(
                site=location_site,
                image=site_image_file,
                notes='Upload session id = {}'.format(upload_session_id),
                form_uploader=WATER_TEMPERATURE_KEY,
            )

        if site_image:
            success_response_image = 'Site image has been uploaded'

        is_daily = False
        new_data = []
        existing_data = []

        # If collector id exist then get the user object
        owner = None
        if owner_id:
            try:
                owner = get_user_model().objects.get(
                    id=int(owner_id))
            except get_user_model().DoesNotExist:
                pass
        else:
            owner = self.request.user

        if source_reference_id:
            try:
                source_reference = SourceReference.objects.get(
                    id=source_reference_id
                )
            except SourceReference.DoesNotExist:
                pass

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
                water_data['minimum'] = (
                    temperature['Minimum'] if is_daily else 0
                )
                water_data['maximum'] = (
                    temperature['Maximum'] if is_daily else 0
                )
                water_data['owner'] = owner
                water_data['uploader'] = self.request.user
                water_data['source_reference'] = source_reference

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
                'message': success_response + '\n' + success_response_image
            })


class WaterTemperatureSiteView(TemplateView):
    template_name = 'water_temperature_single_site.html'
    location_site = LocationSite.objects.none()
    year = None

    def get_context_data(self, **kwargs):
        start_time = time.time()

        context = super(
            WaterTemperatureSiteView, self).get_context_data(**kwargs)
        context['coord'] = [
            self.location_site.get_centroid().x,
            self.location_site.get_centroid().y
        ]
        context['site_code'] = self.location_site.site_code
        context['site_id'] = self.location_site.id
        context['original_site_code'] = self.location_site.legacy_site_code
        context['original_river_name'] = self.location_site.legacy_river_name
        context['site_image'] = SiteImage.objects.filter(
            site=self.location_site)
        context['years'] = list(WaterTemperature.objects.filter(
            location_site=self.location_site
        ).values_list('date_time__year', flat=True).distinct(
            'date_time__year').order_by('date_time__year'))
        if len(context['years']) > 0 :
            context['year'] = int(
                self.year if self.year else context['years'][-1]
            )

        site_description = self.location_site.site_description
        if not site_description:
            site_description = self.location_site.name
        context['site_description'] = site_description
        try:
            context['river'] = self.location_site.river.name
        except AttributeError:
            context['river'] = '-'

        if not self.year:
            year = context['years'][-1]
        else:
            year = int(self.year.strip())

        context['location_site'] = self.location_site
        context['indicators'] = calculate_indicators(self.location_site, year)
        context['execution_time'] = time.time() - start_time
        source_references = (
            WaterTemperature.objects.filter(
                location_site=self.location_site
            ).exclude(
                source_reference__isnull=True
            ).order_by(
                'source_reference').distinct(
            'source_reference').source_references()
        )
        context['source_references'] = json.dumps(source_references)

        return context

    def get(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        self.year = kwargs.get('year', None)
        if not site_id or not request.GET or not request.GET.get(
                'siteId', None):
            raise Http404()
        self.location_site = get_object_or_404(
            LocationSite,
            pk=site_id
        )

        return super(
            WaterTemperatureSiteView, self).get(request, *args, **kwargs)
