# coding=utf-8
import json
import numpy as np
from django.conf import settings
from django.db.models import Count, Case, When
from rest_framework.views import APIView
from rest_framework.response import Response
from haystack.query import SearchQuerySet, SQ
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models.taxon import Taxon
from bims.models.location_site import LocationSite
from bims.serializers.taxon_serializer import TaxonSerializer
from bims.serializers.location_site_serializer import \
    LocationSiteClusterSerializer


class SearchObjects(APIView):
    """API for searching using elasticsearch."""

    def get(self, request):
        sqs = SearchQuerySet()
        search_result = {}

        # Biological records
        query_value = request.GET.get('search')

        if query_value:
            clean_query = sqs.query.clean(query_value)
            settings.ELASTIC_MIN_SCORE = 2
            results = sqs.filter(
                original_species_name=clean_query
            ).models(BiologicalCollectionRecord, Taxon).order_by('-_score')
        else:
            settings.ELASTIC_MIN_SCORE = 0
            results = sqs.all().models(BiologicalCollectionRecord)

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
        taxon_ids = list(set(results.values_list('taxon_gbif', flat=True)))
        bio_ids = results.values_list('model_pk', flat=True)
        location_site_ids = list(
                set(results.values_list('location_site_id', flat=True)))

        taxons = Taxon.objects.filter(id__in=taxon_ids).annotate(
                num_occurences = Count(
                        Case(When(
                                biologicalcollectionrecord__id__in=bio_ids,
                                then=1))))

        location_sites = LocationSite.objects.filter(
                id__in=location_site_ids).annotate(
                num_occurences = Count(Case(When(
                        biological_collection_record__id__in=bio_ids,
                        then=1
                ))))

        context = {
            'record_type': 'bio'
        }
        serializer = TaxonSerializer(taxons, many=True, context=context)
        search_result['biological_collection_record'] = serializer.data
        search_result['location_site'] = LocationSiteClusterSerializer(
                location_sites, many=True, context=context
        ).data
        return Response(search_result)
