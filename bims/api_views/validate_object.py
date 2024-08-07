# coding=utf-8
from bims.models.taxonomy import Taxonomy

from bims.models.location_site import LocationSite
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils.safestring import mark_safe
from bims.models.survey import Survey


class ValidateObject(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        return self.request.user.has_perm('bims.can_validate_site_visit')

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to validate collection data')
        return super(ValidateObject, self).handle_no_permission()

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        try:
            site_visit = Survey.objects.get(pk=object_pk)
            if not site_visit.can_be_validated:
                return HttpResponse(
                    'Site visit cannot be validated',
                    status=status.HTTP_400_BAD_REQUEST
                )
            site_visit.validate()

            site_visit_url = f'/site-visit/detail/{object_pk}/'
            if site_visit.sass_site_visit:
                site_visit_url = f'/sass/view/{site_visit.sass_site_visit.id}/'

            link = f'<a href="{site_visit_url}" target="_blank">View details</a>'
            messages.success(
                self.request,
                mark_safe(f'Site visit validated successfully. {link}.'),
                extra_tags='site_visit_validation'
            )

            return JsonResponse({'status': 'success'})
        except Survey.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )


class ValidateSite(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        site_pk = self.request.GET.get('pk', None)
        if not site_pk:
            return False
        site = LocationSite.objects.get(pk=site_pk)
        return site

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to validate Location site')
        return super(ValidateSite, self).handle_no_permission()

    def get(self, request):
        pk = request.GET.get('pk', None)
        try:
            site = LocationSite.objects.get(pk=pk)
            site.validated = True
            site.save()
            return JsonResponse({'status': 'success'})
        except LocationSite.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )


class ValidateTaxon(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        return self.request.user.has_perm('bims.change_taxonomy')

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to validate Taxon')
        return super(ValidateTaxon, self).handle_no_permission()

    def get(self, request):
        pk = request.GET.get('pk', None)
        try:
            taxon = Taxonomy.objects.get(pk=pk)
            taxon.validate(False)
            return JsonResponse({'status': 'success'})
        except Taxonomy.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
