# coding=utf-8
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from haystack.query import SearchQuerySet, SQ
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models.taxon import Taxon
from bims.serializers.taxon_serializer import TaxonSerializer


class SearchObjects(APIView):
    """API for searching using elasticsearch."""

    def get(self, request):
        sqs = SearchQuerySet()
        search_result = {}

        # Biological records
        query_value = request.GET.get('search')
        if query_value:
            clean_query = sqs.query.clean(query_value)
            results = sqs.filter(
                original_species_name=clean_query
            ).models(BiologicalCollectionRecord)
            settings.ELASTIC_MIN_SCORE = 1
        else:
            results = sqs.all().models(BiologicalCollectionRecord)
            settings.ELASTIC_MIN_SCORE = 0

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
            clean_query_year_from = sqs.query.clean(year_from)
            results = results.filter(
                collection_date_year__gte=clean_query_year_from)

        year_to = request.GET.get('yearTo')
        if year_to:
            clean_query_year_to = sqs.query.clean(year_to)
            results = results.filter(
                collection_date_year__lte=clean_query_year_to)

        months = request.GET.get('months')
        if months:
            qs = months.split(',')
            qs_month = SQ()
            for month in qs:
                clean_query_month = sqs.query.clean(month)
                qs_month.add(
                    SQ(collection_date_month=clean_query_month), SQ.OR)
            results = results.filter(qs_month)

        results = results.filter(
            validated=True
        )
        # group data of biological collection record
        # TODO : Move it to query of haystack and use count aggregations
        records = {}
        sites = {}
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

                if model.site.id not in sites:
                    sites[model.site.id] = {
                        'name': model.site.name,
                        'record_type': 'site',
                        'site_id': model.site.id,
                        'count': 0
                    }
                records[taxon_gbif_id]['count'] += 1

        search_result['biological_collection_record'] = [
            value for key, value in records.iteritems()]
        search_result['location_site'] = [
            value for key, value in sites.iteritems()]

        # Taxon records
        results = sqs.all().models(Taxon)
        if query_value:
            clean_query = sqs.query.clean(query_value)
            results = results.filter(
                common_name=clean_query
            )

        serializer = TaxonSerializer(
            [r.object for r in results], many=True)
        search_result['taxa'] = serializer.data
        return Response(search_result)
