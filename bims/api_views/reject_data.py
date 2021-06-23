# coding=utf-8
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from bims.models.survey import Survey


class RejectData(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        return self.request.user.has_perm('bims.can_validate_site_visit')

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to reject collection data')
        return super(RejectData, self).handle_no_permission()

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        rejection_message = request.GET.get('rejection_message', None)
        try:
            survey = Survey.objects.get(pk=object_pk)
            survey.ready_for_validation = False
            survey.reject(
                rejection_message=rejection_message
            )
            survey.save()

            return JsonResponse({'status': 'success'})
        except Survey.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
