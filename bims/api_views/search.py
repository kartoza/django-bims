# coding=utf-8
from django.db.models import Count, Case, When
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.taxon import Taxon
from bims.models.location_site import LocationSite
from bims.serializers.taxon_serializer import TaxonOccurencesSerializer
from bims.serializers.location_site_serializer import \
    LocationOccurrencesSerializer
from bims.api_views.collection import GetCollectionAbstract


class SearchObjects(APIView):
    """API for searching using elasticsearch.

    Searching by using elastic search.

    This API return 2 object, which are
    - Records:
        Biological records are searched by query are by these keywords
        - original_species_name
        - collectors
        - categories
        - year from and to
        - month
    - Sites
        From records, get location sites list
    """

    def get(self, request):
        query_value = request.GET.get('search')
        results, fuzzy_search = GetCollectionAbstract.apply_filter(
                request, True)
        bio_ids = results.values_list('model_pk', flat=True)
        taxon_ids = list(set(results.values_list('taxon_gbif', flat=True)))
        taxons = Taxon.objects.filter(
            id__in=taxon_ids).annotate(
            num_occurrences=Count(
                Case(When(
                    biologicalcollectionrecord__id__in=bio_ids,
                    then=1)))).order_by('species')

        location_site_ids = list(
            set(results.values_list('location_site_id', flat=True)))
        location_sites = LocationSite.objects.filter(
            id__in=location_site_ids).annotate(
            num_occurrences=Count(Case(When(
                biological_collection_record__id__in=bio_ids,
                then=1)))).order_by('name')

        search_result = dict()
        search_result['fuzzy_search'] = fuzzy_search
        search_result['records'] = TaxonOccurencesSerializer(
            taxons,
            many=True,
            context={'query_value': query_value}).data
        search_result['sites'] = LocationOccurrencesSerializer(
            location_sites, many=True).data
        return Response(search_result)
