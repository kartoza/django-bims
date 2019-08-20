import json

from django.views.generic import TemplateView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import reverse
from django.contrib.gis.geos import Point
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404

from bims.utils.get_key import get_key
from bims.enums.geomorphological_zone import (
    GEOMORPHOLOGICAL_ZONE_CATEGORY_ORDER
)
from bims.models import LocationSite, LocationType
from sass.models import River
from bims.utils.jsonify import json_loads_byteified
from bims.tasks.location_site import update_location_context


class LocationSiteFormView(TemplateView):
    template_name = 'location_site_form_view.html'
    success_message = 'New site has been successfully added'
    catchment_geocontext = None
    geomorphological_group_geocontext = None

    def update_or_create_location_site(self, post_dict):
        location_site = LocationSite.objects.create(**post_dict)
        update_location_context.delay(location_site.id)
        return location_site

    def additional_context_data(self):
        return {
            'username': self.request.user.username,
            'user_id': self.request.user.id
        }

    def get_context_data(self, **kwargs):
        context = super(LocationSiteFormView, self).get_context_data(**kwargs)
        context['geoserver_public_location'] = get_key(
            'GEOSERVER_PUBLIC_LOCATION')
        context['geomorphological_zone_category'] = [
            (g.name, g.value) for g in GEOMORPHOLOGICAL_ZONE_CATEGORY_ORDER
        ]
        context.update(self.additional_context_data())
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(LocationSiteFormView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        owner = request.POST.get('owner', None)
        site_id = request.POST.get('id', None)
        if not owner:
            owner = None
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

        if not latitude or not longitude or not site_code:
            raise Http404()

        latitude = float(latitude)
        longitude = float(longitude)

        geocontext_data = {
            'context_group_values': []
        }
        if catchment_geocontext:
            self.catchment_geocontext = json_loads_byteified(
                catchment_geocontext)
            geocontext_data['context_group_values'].append(
                self.catchment_geocontext)
        if geomorphological_group_geocontext:
            self.geomorphological_group_geocontext = json_loads_byteified(
                geomorphological_group_geocontext
            )
            geocontext_data['context_group_values'].append(
                self.geomorphological_group_geocontext
            )

        if owner:
            try:
                owner = get_user_model().objects.get(
                    id=owner
                )
            except get_user_model().DoesNotExist:
                raise Http404('User does not exist')

        river, river_created = River.objects.get_or_create(
            name=river_name,
            owner=owner
        )

        geometry_point = Point(longitude, latitude)
        location_type, status = LocationType.objects.get_or_create(
            name='PointObservation',
            allowed_geometry='POINT'
        )

        post_dict = {
            'owner': owner,
            'latitude': latitude,
            'longitude': longitude,
            'river': river,
            'site_description': site_description,
            'geometry_point': geometry_point,
            'location_type': location_type,
            'site_code': site_code,
            'location_context_document': geocontext_data
        }

        if site_id and owner:
            # Check if user is only owner but not the creator
            # then user shouldn't be able to change the owner
            try:
                site_object = LocationSite.objects.get(id=site_id)
                if (
                        site_object.owner == request.user and
                        not request.user.is_superuser and
                        site_object.creator != request.user
                ):
                    del post_dict['owner']
            except LocationSite.DoesNotExist:
                pass

        location_site = self.update_or_create_location_site(
            post_dict
        )
        if refined_geomorphological_zone:
            location_site.refined_geomorphological = (
                refined_geomorphological_zone
            )
        location_site.save()
        messages.success(
            self.request,
            self.success_message,
            extra_tags='location_site_form'
        )
        return HttpResponseRedirect(
            '{url}?id={id}'.format(
                url=reverse('location-site-update-form'),
                id=location_site.id
            )
        )


class LocationSiteFormUpdateView(LocationSiteFormView):

    location_site = None
    success_message = 'Site has been successfully updated'

    def update_or_create_location_site(self, post_dict):
        # Update current location context document
        if (self.location_site.location_context_document and
                post_dict['location_context_document']):
            location_context_document = json.loads(
                self.location_site.location_context_document)
            for index, location_context_group in enumerate(
                    location_context_document['context_group_values']):

                if (self.catchment_geocontext and
                        location_context_group['key'] ==
                        self.catchment_geocontext['key']):
                    del location_context_document[
                        'context_group_values'][index]
                    location_context_document['context_group_values'].append(
                        self.catchment_geocontext)

                if (self.geomorphological_group_geocontext and
                        location_context_group['key'] ==
                        self.geomorphological_group_geocontext['key']):
                    del location_context_document[
                        'context_group_values'][index]
                    location_context_document['context_group_values'].append(
                        self.geomorphological_group_geocontext)
            location_context_document['context_group_values'] = list(
                filter(None, location_context_document['context_group_values'])
            )
            post_dict['location_context_document'] = location_context_document

        if self.geomorphological_group_geocontext:
            try:
                post_dict['original_geomorphological'] = (
                    self.geomorphological_group_geocontext[
                        'service_registry_values'][1]['value']
                )
            except KeyError:
                pass

        LocationSite.objects.filter(
            id=self.location_site.id
        ).update(
            **post_dict
        )
        return LocationSite.objects.get(id=self.location_site.id)

    def additional_context_data(self):
        context_data = dict()
        context_data['location_site_lat'] = self.location_site.latitude
        context_data['location_site_long'] = self.location_site.longitude
        context_data['site_code'] = self.location_site.site_code
        context_data['site_description'] = self.location_site.site_description
        context_data['refined_geo_zone'] = (
            self.location_site.refined_geomorphological
        )
        context_data['original_geo_zone'] = (
            self.location_site.original_geomorphological
        )
        context_data['update'] = True
        context_data['allow_to_edit'] = self.allow_to_edit()
        context_data['site_id'] = self.location_site.id
        context_data['legacy_site_code'] = self.location_site.legacy_site_code
        if self.location_site.owner:
            context_data['fullname'] = self.location_site.owner.get_full_name()
            context_data['user_id'] = self.location_site.owner.id
        return context_data

    def allow_to_edit(self):
        """Check if user is allowed to update the data"""
        if self.request.user.is_superuser:
            return True
        if self.location_site.owner:
            if self.request.user.id == self.location_site.owner.id:
                return True
        if self.location_site.creator:
            if self.request.user.id == self.location_site.creator.id:
                return True
        return False

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        location_site_id = self.request.GET.get('id', None)
        if not location_site_id:
            raise Http404('Need location site id')
        try:
            self.location_site = LocationSite.objects.get(id=location_site_id)
        except LocationSite.DoesNotExist:
            raise Http404('Location site does not exist')
        return super(LocationSiteFormUpdateView, self).get(
            request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        # Check if user is the creator of the site or superuser
        location_site_id = self.request.POST.get('id', None)
        if not location_site_id:
            raise Http404('Need location site id')
        try:
            self.location_site = LocationSite.objects.get(id=location_site_id)
        except LocationSite.DoesNotExist:
            raise Http404('Location site does not exist')
        if not self.allow_to_edit():
            raise Http404()
        return super(LocationSiteFormUpdateView, self).post(
            request, *args, **kwargs
        )


class LocationSiteFormDeleteView(UserPassesTestMixin, View):
    location_site = None

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        location_site_id = self.kwargs.get('site_id', None)
        if not location_site_id:
            return False
        try:
            self.location_site = LocationSite.objects.get(
                id=location_site_id
            )
        except LocationSite.DoesNotExist:
            return False
        if self.location_site.creator:
            if self.request.user.id == self.location_site.creator.id:
                return True
        if self.location_site.owner:
            if self.request.user.id == self.location_site.owner.id:
                return True
        return False

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        location_site = get_object_or_404(
            LocationSite,
            id=self.kwargs.get('site_id', None)
        )
        location_site.delete()
        messages.success(
            self.request,
            'Location site successfully deleted',
            extra_tags='location_site_form'
        )
        return HttpResponseRedirect(reverse('location-site-form'))
