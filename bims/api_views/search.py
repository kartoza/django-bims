# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '07/06/18'

from rest_framework.views import APIView
from rest_framework.response import Response
from bims.documents import BiologicalCollectionRecordDocument
from bims.serializers.bio_collection_record_doc_serializer import \
    BiologicalCollectionRecordDocSerializer


class SearchObjects(APIView):
    """API for searching using elasticsearch."""

    def get(self, request, original_species_name):
        results = BiologicalCollectionRecordDocument.search().query(
            "match", original_species_name=original_species_name)

        data = {}
        if results.count() > 0:
            serializer = \
                BiologicalCollectionRecordDocSerializer(results, many=True)
            return Response(serializer.data)
        else:
            data['results'] = 'Not Found'
            return Response(data)
