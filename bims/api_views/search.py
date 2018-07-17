# coding=utf-8
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from haystack.query import SearchQuerySet, SQ
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models.location_site import LocationSite
from bims.models.taxon import Taxon
from bims.serializers.location_site_serializer import LocationSiteSerializer
from bims.serializers.taxon_serializer import TaxonSerializer


class SearchObjects(APIView):
    """API for searching using elasticsearch."""

    def get(self, request):
        query_value = request.GET.get('search')
        sqs = SearchQuerySet()
        clean_query = sqs.query.clean(query_value)
        search_result = {}

        # Biological records
        results = sqs.filter(
            original_species_name=clean_query
        ).models(BiologicalCollectionRecord)

        query_collector = request.GET.get('collector')
        query_category = request.GET.get('category')

        if query_collector:
            qs_collector = SQ()
            qs = json.loads(query_collector)
            for query in qs:
                qs_collector.add(SQ(collector=query), SQ.OR)
            results = results.filter(qs_collector)

        if query_category:
            qs_category = SQ()
            qs = json.loads(query_category)
            for query in qs:
                qs_category.add(SQ(category=query), SQ.OR)
            results = results.filter(qs_category)

        year_from = request.GET.get('yearFrom')
        if year_from:
            print(year_from)
            clean_query_year_from = sqs.query.clean(year_from)
            results = results.filter(
                collection_date__year__gte=clean_query_year_from)

        year_to = request.GET.get('yearTo')
        if year_to:
            print(year_to)
            clean_query_year_to = sqs.query.clean(year_to)
            results = results.filter(
                collection_date__year__lte=clean_query_year_to)

        months = request.GET.get('months')
        if months:
            qs = months.split(',')
            qs_month = SQ()
            for month in qs:
                clean_query_month = sqs.query.clean(month)
                qs_month.add(SQ(collection_date__month=clean_query_month), SQ.OR)
            results = results.filter(collection_date__month=qs_month)

        # group data of biological collection record
        # TODO : Move it to query of haystack and use count aggregations
        records = {}
        for r in results:
            model = r.object
            if model.taxon_gbif_id:
                taxon_gbif_id = model.taxon_gbif_id.id
                if taxon_gbif_id not in records:
                    records[taxon_gbif_id] = {
                        'common_name': model.taxon_gbif_id.common_name,
                        'record_type': 'bio',
                        'taxon_gbif_id': taxon_gbif_id,
                        'count': 0
                    }
                records[taxon_gbif_id]['count'] += 1

        search_result['biological_collection_record'] = [
            value for key, value in records.iteritems()]

        # Taxon records
        results = sqs.filter(
            common_name=clean_query
        ).models(Taxon)

        serializer = TaxonSerializer(
            [r.object for r in results], many=True)
        search_result['taxa'] = serializer.data

        # Sites records
        results = sqs.filter(
            name=clean_query
        ).models(LocationSite)

        serializer = LocationSiteSerializer(
            [r.object for r in results], many=True)
        search_result['location_site'] = serializer.data
        return Response(search_result)
