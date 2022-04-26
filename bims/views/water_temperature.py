import codecs
import csv
import json
import time
import ast
from datetime import datetime

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.cache import cache
from django.db.models import Case, When

from bims.models.location_context import LocationContext
from braces.views import LoginRequiredMixin
from django.utils.timezone import make_aware
from django.contrib.auth import get_user_model
from django.views import View
import logging
from django.http import JsonResponse, HttpResponseForbidden
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.http import Http404

from bims.models.basemap_layer import BaseMapLayer
from bims.tasks.water_temperature import process_water_temperature_data
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
WATER_TEMPERATURE_CACHE_KEY = 'WATER_TEMPERATURE_DATA_PROCESS'


class WaterTemperatureBaseView(
    UserPassesTestMixin, TemplateView, SessionFormMixin):
    template_name = ''
    permission = ''

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        return self.request.user.has_perm(self.permission)

    def get_context_data(self, **kwargs):
        context = super(
            WaterTemperatureBaseView, self).get_context_data(**kwargs)
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

        return super(
            WaterTemperatureBaseView, self).get(request, *args, **kwargs)


class WaterTemperatureEditView(WaterTemperatureBaseView):
    template_name = 'water_temperature_edit_form.html'
    permission = 'bims.update_watertemperature'
    water_temperature = WaterTemperature.objects.none()
    year = None
    location_site = None

    def get(self, request, *args, **kwargs):
        self.year = request.GET.get('year', None)
        site_id = request.GET.get('siteId', None)
        if site_id:
            self.location_site = get_object_or_404(
                LocationSite,
                pk=site_id
            )
        else:
            raise Http404()
        self.water_temperature = WaterTemperature.objects.filter(
            date_time__year=self.year,
            location_site=self.location_site
        )
        if not self.water_temperature.exists():
            raise Http404('Water temperature does not exist')
        return super(
            WaterTemperatureEditView, self
        ).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(
            WaterTemperatureEditView, self
        ).get_context_data(**kwargs)
        if not self.request.user.is_superuser:
            self.water_temperature = self.water_temperature.filter(
                owner=self.request.user,
            )
        ctx['total_data'] = self.water_temperature.count()
        ctx['site_image'] = SiteImage.objects.filter(
            owner=self.request.user,
            site=self.location_site,
            date__year=self.year
        )
        ctx['owner'] = self.water_temperature.first().owner
        ctx['source_reference'] = (
            SourceReference.objects.filter(
                id__in=self.water_temperature.values('source_reference'))
        )
        ctx['year'] = self.year

        return ctx


class WaterTemperatureView(WaterTemperatureBaseView):
    """View for water temperature form"""
    template_name = 'water_temperature_form.html'
    permission = 'bims.create_watertemperature'


class WaterTemperatureValidateView(LoginRequiredMixin, View):
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

        edit = ast.literal_eval(
            request.POST.get('edit', 'false').capitalize()
        )

        if not water_file and edit:
            return JsonResponse({
                'status': 'success',
                'message': 'Water temperature is validated',
            })

        if not date_format or not interval or not start_time:
            raise Http404('Missing required fields')

        if float(interval) != 24:
            date_format = date_format + ' %H:%M'
        else:
            is_daily = True

        row = 2
        reader = csv.DictReader(codecs.iterdecode(water_file, 'utf-8'))
        headers = reader.fieldnames
        data = list(reader)
        date_field = 'Date Time' if 'Date Time' in headers else 'Date'
        value_key = ''

        if is_daily:
            if not any(header in ['Mean', 'Minimum', 'Maximum'] for header in
                       headers):
                self.add_error_messages(
                    row,
                    'Missing minimum and maximum data value'
                )
                finished = True
            else:
                value_key = 'Mean'
        else:
            if 'Water temperature' not in headers:
                self.add_error_messages(
                    row - 1,
                    'Missing "Water temperature" header'
                )
                finished = True
            else:
                value_key = 'Water temperature'

        if not finished:
            for temperature_data in data:
                # Check date format
                try:
                    date_string = temperature_data[date_field]
                    if len(date_string.split(':')) > 2 and ':%S' not in date_format:
                        date_format += ':%S' # Add second
                    date = datetime.strptime(date_string, date_format)
                    value = temperature_data[value_key]

                    if value:
                        try:
                            float(value)
                        except ValueError:
                            self.add_error_messages(
                                row,
                                '{} data must be a decimal.'.format(
                                    value_key
                                )
                            )
                            continue

                    # Check interval
                    if not is_daily:
                        time_string = date.strftime('%H:%M')
                        if len(times) == 0 and time_string != start_time:
                            self.add_error_messages(
                                row,
                                'Non daily data should start at {} but get {}'.format(
                                    start_time, time_string
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
                                    'Non daily data should end at {} but get {}'.format(
                                        end_time, time_string
                                    )
                                )
                            if RECORDS_PER_INTERVAL[interval] > len(times) > 0:
                                self.add_error_messages(
                                    row - 1,
                                    'Data for {} are missing {} rows'.format(
                                        times[-1].date(),
                                        RECORDS_PER_INTERVAL[interval] - len(times)
                                    )
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


class WaterTemperatureUploadView(LoginRequiredMixin, View):
    location_site = None
    upload_task = None

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseForbidden()

        upload_session_id = request.POST.get('upload_session_id', None)
        edit = ast.literal_eval(
            request.POST.get('edit', 'false').capitalize()
        )
        location_site = LocationSite.objects.get(
            pk=request.POST.get('site-id', None)
        )
        source_reference_id = request.POST.get('source_reference', '')
        site_image_file = request.FILES.get('site_image')
        success_response = ''
        owner_id = request.POST.get('owner_id', '').strip()
        site_image = None
        source_reference = None
        site_image_updated = False

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

        if site_image_file:
            site_image, _ = SiteImage.objects.get_or_create(
                owner=owner,
                uploader=self.request.user,
                site=location_site,
                image=site_image_file,
                form_uploader=WATER_TEMPERATURE_KEY
            )
            site_image_updated = True

        if edit:
            site_image_date = None
            site_image_to_delete = (
                request.POST.get('site_image_to_delete', None)
            )
            year = (
                request.POST.get('year', None)
            )
            previous_source_reference_id = (
                request.POST.get('previous_source_reference_id', '')
            )

            water_temperature = WaterTemperature.objects.filter(
                location_site=location_site
            )
            if year:
                water_temperature = water_temperature.filter(
                    date_time__year=year
                )

            if not water_temperature.filter(owner__id=owner_id).exists():
                water_temperature.update(owner=owner_id)
                success_response += (
                    ' Owner is updated. '
                )

            if not upload_session_id or upload_session_id == 'undefined':
                if previous_source_reference_id:
                    water_temperature = water_temperature.filter(
                        location_site=location_site
                    )

                if not self.request.user.is_superuser:
                    water_temperature = water_temperature.filter(
                        owner=owner
                    )
                if water_temperature.exists():
                    site_image_date = water_temperature.first().date_time
                else:
                    logger.error('Water temperature does not exist')
                    return
            if source_reference_id != previous_source_reference_id:
                water_temperature.update(
                    source_reference=source_reference
                )
                success_response += (
                    ' Source reference is updated. '
                )

            if site_image_to_delete:
                site_images = SiteImage.objects.filter(
                    id__in=site_image_to_delete.split(',')
                )
                if site_images.exists():
                    site_image_date = site_images.first().image_date
                    site_images.delete()
                site_image_updated = True

            if site_image and site_image_date:
                site_image.date = site_image_date
                site_image.save()

        if site_image_updated:
            success_response += 'Site image is updated\n'

        if upload_session_id and upload_session_id != 'undefined':
            upload_session = UploadSession.objects.get(id=upload_session_id)
            task = process_water_temperature_data.delay(
                upload_session_id,
                site_image.id if site_image else None,
                self.request.user.id,
                request.POST.dict()
            )
            upload_session.token = task.id
            upload_session.save()

            return JsonResponse({
                'status': 'PENDING',
                'message': 'Processing',
                'task': upload_session.token
            })
        else:
            return JsonResponse({
                'status': 'SUCCESS',
                'message': success_response,
                'task': None
            })


class WaterTemperatureSiteView(TemplateView):
    template_name = 'water_temperature_single_site.html'
    location_site = LocationSite.objects.none()
    location_context = None
    year = None
    start_date = None
    end_date = None

    def get_context_data(self, **kwargs):
        start_time = time.time()
        context = super(
            WaterTemperatureSiteView, self).get_context_data(**kwargs)

        water_temperature_data = WaterTemperature.objects.filter(
            location_site=self.location_site
        )
        if not water_temperature_data.exists():
            raise Http404('Does not exist')

        context['years'] = list(
            water_temperature_data.values_list(
                'date_time__year', flat=True).distinct(
            'date_time__year').order_by('date_time__year'))

        if self.year and isinstance(self.year, str):
            self.year = int(self.year.strip())

        if not self.year and len(context['years']) > 0:
            self.year = int(context['years'][-1])

        if self.start_date and self.end_date:
            self.start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
            self.end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
            water_temperature_data = water_temperature_data.filter(
                date_time__gt=self.start_date,
                date_time__lt=self.end_date
            )
        elif self.year:
            water_temperature_data = water_temperature_data.filter(
                date_time__year=self.year
            )

        context['is_owner'] = water_temperature_data.filter(
            owner=self.request.user
        ).exists() if not self.request.user.is_anonymous else False

        context['coord'] = [
            self.location_site.get_centroid().x,
            self.location_site.get_centroid().y
        ]
        context['site_code'] = self.location_site.site_code
        context['site_id'] = self.location_site.id
        context['original_site_code'] = self.location_site.legacy_site_code
        context['original_river_name'] = self.location_site.legacy_river_name
        site_images = SiteImage.objects.filter(
            site=self.location_site
        ).order_by('date')

        if len(context['years']) > 0 :
            context['year'] = int(
                self.year if self.year else context['years'][-1]
            )

        context['site_image'] = site_images
        site_description = self.location_site.site_description
        if not site_description:
            site_description = self.location_site.name
        context['site_description'] = site_description
        try:
            context['river'] = self.location_site.river.name
        except AttributeError:
            context['river'] = '-'

        water_temperature_data =  water_temperature_data.order_by(
            'date_time'
        )

        if self.year:
            if water_temperature_data:
                context['indicators'] = calculate_indicators(
                    self.location_site, self.year, False,
                    water_temperature_data)
            else:
                context['indicators'] = []

        context['location_site'] = self.location_site
        context['execution_time'] = time.time() - start_time
        context['start_date'] = (
            self.start_date if self.start_date else
                water_temperature_data.first().date_time
        )
        context['end_date'] = (
            self.end_date if self.end_date else
                water_temperature_data.last().date_time
        )
        source_references = (
            water_temperature_data.exclude(
                source_reference__isnull=True
            ).order_by(
                'source_reference').distinct(
                'source_reference').source_references()
        )
        context['source_references'] = json.dumps(source_references)

        context['river_catchments'] = json.dumps(
            self.location_context.values_from_group(
                'river_catchment_areas_group'
        ))
        context['wma'] = (
            json.dumps(self.location_context.values_from_group(
                'water_management_area'
            ))
        )
        context['geomorphological_group'] = (
            json.dumps(self.location_context.values_from_group(
                'geomorphological_group'
            ))
        )
        context['river_ecoregion_group'] = (
            json.dumps(self.location_context.values_from_group(
                'river_ecoregion_group'
            ))
        )
        context['freshwater_ecoregion_of_the_world'] = (
            json.dumps(self.location_context.values_from_group(
                'freshwater_ecoregion_of_the_world'
            ))
        )
        context['political_boundary'] = (
            json.dumps(self.location_context.values_from_group(
                'province'
            ))
        )
        refined_geomorphological = '-'
        if self.location_site.refined_geomorphological:
            refined_geomorphological = (
                self.location_site.refined_geomorphological
            )
        context['refined_geomorphological'] = refined_geomorphological

        return context

    def get(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        self.year = kwargs.get('year', None)
        self.start_date = request.GET.get('startDate', None)
        self.end_date = request.GET.get('endDate', None)
        if not site_id or not request.GET or not request.GET.get(
                'siteId', None):
            raise Http404()
        self.location_site = get_object_or_404(
            LocationSite,
            pk=site_id
        )
        self.location_context = LocationContext.objects.filter(
            site=self.location_site
        )

        return super(
            WaterTemperatureSiteView, self).get(request, *args, **kwargs)
