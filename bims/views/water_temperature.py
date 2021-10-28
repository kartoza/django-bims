import csv
from datetime import datetime
from braces.views import LoginRequiredMixin
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

    def extra_post(self, post):
        """
        Override this method to process the POST request.
        :param post: POST request
        """
        return


class WaterTemperatureUploadView(View, LoginRequiredMixin):
    location_site = None
    category = 'water_temperature'
    upload_task = None

    def post(self, request, *args, **kwargs):

        if not request.is_ajax():
            return HttpResponseForbidden()
        owner_id = request.POST.get('owner_id', '').strip()
        interval = request.POST.get('interval')
        water_file = request.FILES.get('water_file')
        date_format = request.POST.get('format')

        if float(interval) != 24:
            date_format = date_format + ' %H:%M'

        upload_session = UploadSession.objects.create(
            uploader=request.user,
            process_file=water_file,
            uploaded_at=datetime.now(),
            category=self.category
        )
        if self.upload_task:
            self.upload_task.delay(upload_session.id)

        with open(upload_session.process_file.path) as file:
            reader = csv.DictReader(file)
            data = list(reader)
            real_row = len(data)
            try:
                date_start = datetime.strptime(data[0]['Date Time'], date_format)
                date_end = datetime.strptime(data[-1]['Date Time'], date_format)
            except ValueError:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'Please check your date format'
                })
            except KeyError:
                try:
                    date_start = datetime.strptime(data[0]['Date'], date_format)
                    date_end = datetime.strptime(data[-1]['Date'], date_format)
                except ValueError:
                    return JsonResponse({
                        'status': 'failed',
                        'message': 'Please check your date format'
                    })
            row_by_date = (date_end - date_start).days * int(24 / float(interval))

            if real_row != row_by_date:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'Date start: {0} \n Date end: {1} \n ' \
                               'Logging interval: {2} \n' \
                               'The number of row should be: {3} \n' \
                               'But there is: {4} in the file'.format(
                        date_start.strftime(date_format),
                        date_end.strftime(date_format),
                        interval,
                        row_by_date,
                        real_row,
                        real_row - row_by_date)
                })

            for temperature in data:
                if int(interval) == 24:
                    if any(header in ['Mean', 'Minimum', 'Maximum'] for header in reader.fieldnames):
                        water_temp, created = WaterTemperature.objects.get_or_create(
                            date_time=datetime.strptime(temperature['Date'], date_format),
                            location_site=LocationSite.objects.get(pk=request.POST.get('site-id', None)),
                            is_daily=True,
                            value=temperature['Mean']
                        )

                    else:
                        return JsonResponse({
                            'status': 'failed',
                            'message': 'Missing minimum amd maximum data value'
                        })

                else:
                    water_temp, created = WaterTemperature.objects.get_or_create(
                        date_time=datetime.strptime(temperature['Date Time'], date_format),
                        location_site=LocationSite.objects.get(pk=request.POST.get('site-id', None)),
                        is_daily=False,
                        value=temperature['Water temperature']

                    )
                try:
                    water_temp.value = temperature['Mean']
                    water_temp.minimum = temperature['Minimum']
                    water_temp.maximum = temperature['Maximum']

                except KeyError:
                    water_temp.value = temperature['Water temperature']

                water_temp.source_file = upload_session.process_file.path
                water_temp.uploader = self.request.user
                water_temp.owner = get_user_model().objects.get(
                    id=int(owner_id))
                water_temp.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Water temperature date being uploaded. Thank you'
            })
