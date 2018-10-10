# coding=utf-8
import os, json, hashlib, errno
from django.db.models import Count, Case, When
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.taxon import Taxon
from bims.models.location_site import LocationSite
from bims.serializers.taxon_serializer import TaxonOccurencesSerializer
from bims.serializers.location_site_serializer import \
    LocationOccurrencesSerializer
from bims.api_views.collection import GetCollectionAbstract
from bims.tasks.search import search_collection
from bims.models import SearchProcess


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
    @staticmethod
    def process_search(
            collection_result,
            query_value,
            bio_ids=[],
            taxon_ids=[],
            location_site_ids=[]):

        for collection in collection_result:
            if collection.model_pk and \
                    collection.model_pk not in bio_ids:
                bio_ids.append(collection.model_pk)
            if collection.taxon_gbif and \
                    collection.taxon_gbif not in taxon_ids:
                taxon_ids.append(collection.taxon_gbif)
            if collection.location_site_id and \
                    collection.location_site_id not in location_site_ids:
                location_site_ids.append(collection.location_site_id)

        taxons = Taxon.objects.filter(
            id__in=taxon_ids
        ).annotate(
            num_occurrences=Count(Case(When(
                biologicalcollectionrecord__id__in=bio_ids,
                then=1
            )))
        ).order_by('species')

        location_sites = LocationSite.objects.filter(
            id__in=location_site_ids
        ).annotate(
            num_occurrences=Count(Case(When(
                biological_collection_record__id__in=bio_ids,
                then=1
            )))).order_by('name')

        record_results = TaxonOccurencesSerializer(
            taxons,
            many=True,
            context={
                'query_value': query_value
            }).data

        sites_results = LocationOccurrencesSerializer(
            location_sites,
            many=True,
            context={
                'query_value': query_value
            }).data

        ids = {
            'bio_ids': bio_ids,
            'taxon_ids': taxon_ids,
            'location_site_ids': location_site_ids
        }
        return record_results, sites_results, ids

    @staticmethod
    def process_sites_search(site_results, location_site_ids, query):
        sites = LocationOccurrencesSerializer(
                GetCollectionAbstract.queryset_gen(
                        site_results,
                        exlude_ids=location_site_ids),
                many=True,
                context={'query_value': query}
        ).data
        return sites

    def get(self, request):
        query_value = request.GET.get('search')
        filters = request.GET
        search_result = dict()
        search_result['sites'] = []
        search_result['records'] = []
        search_uri = request.build_absolute_uri()
        folder = 'search_results'

        search_process, created = SearchProcess.objects.get_or_create(
                category=folder,
                query=search_uri
        )

        if not created and search_process.file_path:
            if os.path.exists(search_process.file_path):
                raw_data = open(search_process.file_path)
                if search_process.finished:
                    return Response(json.load(raw_data))
            else:
                if search_process.finished:
                    search_process.finished = False
                    search_process.save()

        # Search collection
        collection_results, \
            site_results, \
            fuzzy_search = GetCollectionAbstract.apply_filter(
                query_value,
                filters,
                ignore_bbox=True)

        # Check if filename exists
        data_for_filename = dict(filters)
        data_for_filename['collection_results_length'] = len(
                collection_results)
        data_for_filename['site_results_length'] = len(site_results)
        process_id = hashlib.md5(
                json.dumps(data_for_filename, sort_keys=True)
        ).hexdigest()
        path_folder = os.path.join(settings.MEDIA_ROOT, folder)
        path_file = os.path.join(path_folder, process_id)

        search_process.process_id = process_id
        search_process.save()

        try:
            os.mkdir(path_folder)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass
        search_collection.delay(
                query_value,
                filters,
                path_file,
                process_id
        )

        if os.path.exists(path_file):
            raw_data = open(path_file)
            if raw_data:
                json_data = json.load(raw_data)
                return Response(json_data)

        return Response({
            'status': 'processing',
            'process': process_id
        })
