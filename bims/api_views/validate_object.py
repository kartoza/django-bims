# coding=utf-8
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
