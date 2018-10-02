# coding=utf-8
from django.http.response import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.views import APIView, Response
from rest_framework import status
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.bio_collection_serializer import (
    BioCollectionSerializer,
)
from bims.permissions.api_permission import IsValidator, AllowedTaxon


class GetNonValidatedRecords(APIView):

    permission_classes = [IsValidator, ]
    page_limit = 5

    def get(self, request):
        try:
            allowed_taxon = AllowedTaxon()
            taxon_list = allowed_taxon.get(request.user)
            records = BiologicalCollectionRecord.objects.filter(
                    validated=False,
                    ready_for_validation=True,
                    taxon_gbif_id__in=taxon_list
            )

            paginator = Paginator(records, self.page_limit)
            page = request.GET.get('page')

            try:
                records = paginator.page(page)
            except PageNotAnInteger:
                records = paginator.page(1)
            except EmptyPage:
                records = paginator.page(paginator.num_pages)

            serializer = BioCollectionSerializer(
                    records,
                    many=True
            )
            return Response(serializer.data)
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
