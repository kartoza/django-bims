# coding=utf-8
from bims.models.location_site import LocationSite
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
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
            site_visit.validated = True
            site_visit.ready_for_validation = False
            site_visit.save()

            messages.add_message(
                request,
                messages.SUCCESS,
                'Object validated successfully.',
                'site_visit_validation'
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
