# coding=utf-8
import os
import json
import hashlib
import errno
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
from bims.utils.highlighter import CustomHighlighter

COUNT_LABEL = 'c'
NAME_LABEL = 'n'
HIGHLIGHTER_LABEL = 'h'


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
            taxon_results,
            site_results):

        highlighter = CustomHighlighter(query_value, max_length=100)

        # calculate taxon
        for collection in collection_result:
            if collection.taxon_gbif not in taxon_results:
                taxon_results[collection.taxon_gbif] = {
                    COUNT_LABEL: 1,
                    NAME_LABEL: collection.original_species_name,
                    HIGHLIGHTER_LABEL: highlighter.highlight(
                            collection.original_species_name)
                }
            else:
                taxon_results[collection.taxon_gbif][COUNT_LABEL] += 1

            if collection.location_site_id not in site_results:
                site_results[collection.location_site_id] = {
                    COUNT_LABEL: 1,
                    NAME_LABEL: collection.location_site_name
                }
            else:
                site_results[collection.location_site_id][COUNT_LABEL] += 1
        return taxon_results, site_results

    @staticmethod
    def process_sites_search(sites, site_results, query):
        highlighter = CustomHighlighter(query, max_length=100)
        for site in sites:
            if site.location_site_id not in site_results:
                site_results[site.location_site_id] = {
                    COUNT_LABEL: 0,
                    NAME_LABEL: highlighter.highlight(
                            site.location_site_name
                    )
                }
            else:
                continue
        return site_results

    def get(self, request):
        query_value = request.GET.get('search')
        filters = request.GET
        search_result = dict()
        search_result['sites'] = []
        search_result['records'] = []
        search_uri = request.build_absolute_uri()
        folder = 'search_results'
        status = {
            'current_status': 'processing'
        }

        search_process, created = SearchProcess.objects.get_or_create(
                category=folder,
                query=search_uri
        )

        if not created and search_process.file_path:
            if os.path.exists(search_process.file_path):
                raw_data = open(search_process.file_path)
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
        data_for_filename = dict()
        data_for_filename['search_uri'] = search_uri
        data_for_filename['collection_results_length'] = len(
                collection_results)
        data_for_filename['site_results_length'] = len(site_results)
        process_id = hashlib.md5(
                json.dumps(data_for_filename, sort_keys=True)
        ).hexdigest()
        path_folder = os.path.join(settings.MEDIA_ROOT, folder)
        path_file = os.path.join(path_folder, process_id)

        status['process'] = process_id
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
            'status': status
        })
