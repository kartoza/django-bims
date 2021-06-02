# coding=utf-8
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.permissions.api_permission import AllowedTaxon


class RejectCollectionData(UserPassesTestMixin, LoginRequiredMixin, APIView):

    def test_func(self):
        allowed_taxon = AllowedTaxon()
        taxon_list = allowed_taxon.get(self.request.user)
        collection_pk = self.request.GET.get('pk', None)
        if not collection_pk:
            return False
        collection = BiologicalCollectionRecord.objects.get(pk=collection_pk)
        return collection.taxonomy in taxon_list

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
