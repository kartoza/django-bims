# coding=utf8
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.taxon import Taxon
from bims.serializers.taxon_serializer import \
    TaxonSerializer
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord


class TaxonDetail(APIView):
    """
    Retrieve a taxon instance.
    """

    def get_object(self, pk):
        try:
            return Taxon.objects.get(pk=pk)
        except Taxon.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        taxon = self.get_object(pk)
        serializer = TaxonSerializer(taxon)
        data = serializer.data

        records = BiologicalCollectionRecord.objects.filter(
            taxon_gbif_id=taxon
        )
        data['count'] = records.count()
        return Response(data)
