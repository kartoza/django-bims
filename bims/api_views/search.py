# coding=utf-8

from rest_framework.views import APIView
from rest_framework.response import Response
from haystack.query import SearchQuerySet
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.serializers.bio_collection_record_doc_serializer import \
    BiologicalCollectionRecordDocSerializer


class SearchObjects(APIView):
    """API for searching using elasticsearch."""

    def get(self, request, query_value):
        sqs = SearchQuerySet()
        clean_query = sqs.query.clean(query_value)
        results = []
        results.extend(
                sqs.filter(
                        original_species_name=clean_query
                ).models(BiologicalCollectionRecord)
        )

        results.extend(
                sqs.filter(
                        collector=clean_query
                ).models(BiologicalCollectionRecord)
        )

        data = {}
        if len(results) > 0:
            serializer = \
                BiologicalCollectionRecordDocSerializer(
                        [result.object for result in results], many=True)
            return Response(serializer.data)
        else:
            data['results'] = 'Not Found'
            return Response(data)
