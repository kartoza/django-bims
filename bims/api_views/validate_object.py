# coding=utf-8
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.utils.user_permissions import ValidatorRequiredMixin


class ValidateObject(ValidatorRequiredMixin, APIView):

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        try:
            object = BiologicalCollectionRecord.objects.get(pk=object_pk)
            object.validated = True
            object.save()
            return JsonResponse({'status': 'success'})
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
