# coding=utf-8
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response
from django.http import HttpResponse
from rest_framework import status
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.bio_collection_serializer import BioCollectionSerializer


class GetBioRecords(LoginRequiredMixin, APIView):

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        try:
            object = BiologicalCollectionRecord.objects.get(pk=object_pk)
            serializer = BioCollectionSerializer(object)
            return Response(serializer.data)
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
