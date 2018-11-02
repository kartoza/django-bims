# coding=utf-8
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from bims.models.biological_collection_record import BiologicalCollectionRecord


class RejectCollectionData(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        return self.request.user.has_perm('bims.can_validate_data')

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to validate collection data')
        return super(RejectCollectionData, self).handle_no_permission()

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        rejection_message = request.GET.get('rejection_message', None)
        try:
            collection = BiologicalCollectionRecord.objects.get(pk=object_pk)
            collection.reject(
                rejection_message=rejection_message
            )
            return JsonResponse({'status': 'success'})
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
