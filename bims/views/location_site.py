import json

from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import reverse
from django.contrib.gis.geos import Point

from bims.utils.get_key import get_key
from bims.enums.geomorphological_zone import GeomorphologicalZoneCategory
from bims.models import LocationSite, LocationType
from sass.models import River
from bims.utils.jsonify import json_loads_byteified

class LocationSiteFormView(TemplateView):
    template_name = 'location_site_form_view.html'

    def get_context_data(self, **kwargs):
        context = super(LocationSiteFormView, self).get_context_data(**kwargs)
        context['geoserver_public_location'] = get_key(
            'GEOSERVER_PUBLIC_LOCATION')
        context['geomorphological_zone_category'] = [
            (g.name, g.value) for g in GeomorphologicalZoneCategory
        ]
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(LocationSiteFormView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        collector = request.POST.get('collector', None)
        latitude = request.POST.get('latitude', None)
        longitude = request.POST.get('longitude', None)
        refined_geomorphological_zone = request.POST.get(
            'refined_geomorphological_zone',
            None
        )
        river_name = request.POST.get('river', None)
        site_code = request.POST.get('site_code', None)
        site_description = request.POST.get('site_description', None)
        catchment_geocontext = request.POST.get('catchment_geocontext', None)
        geomorphological_group_geocontext = request.POST.get(
            'geomorphological_group_geocontext',
            None
        )

        if not collector or not latitude or not longitude or not site_code:
            raise Http404()

        latitude = float(latitude)
        longitude = float(longitude)

        if catchment_geocontext:
            catchment_geocontext = json_loads_byteified(catchment_geocontext)
        if geomorphological_group_geocontext:
            geomorphological_group_geocontext = json_loads_byteified(
                geomorphological_group_geocontext
            )
        geocontext_data = {
            'context_group_values': [
                catchment_geocontext,
                geomorphological_group_geocontext
            ]
        }

        try:
            collector = get_user_model().objects.get(
                id=collector
            )
        except get_user_model().DoesNotExist:
            raise Http404('User does not exist')

        river, river_created = River.objects.get_or_create(
            name=river_name,
            owner=collector
        )

        geometry_point = Point(longitude, latitude)
        location_type, status = LocationType.objects.get_or_create(
            name='PointObservation',
            allowed_geometry='POINT'
        )

        location_site = LocationSite.objects.create(
            creator=collector,
            latitude=latitude,
            longitude=longitude,
            river=river,
            site_description=site_description,
            geometry_point=geometry_point,
            location_type=location_type,
            site_code=site_code,
            location_context_document=geocontext_data
        )

        if refined_geomorphological_zone:
            location_site.refined_geomorphological = (
                refined_geomorphological_zone
            )
            location_site.save()

        messages.success(
            self.request,
            'New site has been successfully added'
        )

        return HttpResponseRedirect(reverse('location-site-form'))
