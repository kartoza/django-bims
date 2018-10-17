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
from bims.api_views.collection import GetCollectionAbstract


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

    def get(self, request):
        query_value = request.GET.get('search')
        filters = request.GET

        # Search collection
        collection_results, \
        site_results, \
        fuzzy_search = GetCollectionAbstract.apply_filter(
                query_value,
                filters,
                ignore_bbox=True)

        try:
            serializer = BioCollectionSerializer(
                    [q.object for q in collection_results],
                    many=True)
            return Response(serializer.data)
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
