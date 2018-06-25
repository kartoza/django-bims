# coding=utf-8

from rest_framework.views import APIView
from rest_framework.response import Response
from haystack.query import SearchQuerySet
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models.location_site import LocationSite
from bims.models.taxon import Taxon
from bims.serializers.bio_collection_record_doc_serializer import \
    BiologicalCollectionRecordDocSerializer
from bims.serializers.location_site_serializer import LocationSiteSerializer
from bims.serializers.taxon_serializer import TaxonSerializer


class SearchObjects(APIView):
    """API for searching using elasticsearch."""

    def get(self, request, query_value):
        sqs = SearchQuerySet()
        clean_query = sqs.query.clean(query_value)
        result = {}

        # Biological records
        results = sqs.filter(
            original_species_name=clean_query
        ).models(BiologicalCollectionRecord)
        serializer = BiologicalCollectionRecordDocSerializer(
            [result.object for result in results], many=True)

        result['biological_collection_record'] = serializer.data

        # Taxon records
        results = sqs.filter(
            common_name=clean_query
        ).models(Taxon)
        serializer = TaxonSerializer(
            [result.object for result in results], many=True)
        result['taxa'] = serializer.data

        # Sites records
        results = sqs.filter(
            name=clean_query
        ).models(LocationSite)
        serializer = LocationSiteSerializer(
            [result.object for result in results], many=True)
        result['location_site'] = serializer.data
        return Response(result)
