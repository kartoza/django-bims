# coding=utf-8
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response
from django.http import HttpResponse
from rest_framework import status
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.bio_collection_serializer import (
    BioCollectionSerializer,
    BioCollectionDetailSerializer,
)


class GetBioRecordDetail(LoginRequiredMixin, APIView):

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        try:
            object = BiologicalCollectionRecord.objects.get(pk=object_pk)
            serializer = BioCollectionDetailSerializer(object)
            return Response(serializer.data)
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )


class GetBioRecords(APIView):

    def get(self, request, taxon_id):
        try:
            records = BiologicalCollectionRecord.objects.filter(
                taxon_gbif_id=taxon_id
            )
            serializer = BioCollectionSerializer(records, many=True)
            return Response(serializer.data)
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
