# coding=utf-8
import os
import json
import hashlib
import errno
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.api_views.collection import GetCollectionAbstract
from bims.tasks.search import search_collection
from bims.models import SearchProcess

COUNT_LABEL = 'c'
NAME_LABEL = 'n'
HIGHLIGHTER_LABEL = 'h'
COLLECTION_IDS = 'i'


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

        # calculate taxon
        for collection in collection_result:
            if collection.taxonomy not in taxon_results:
                taxon_results[collection.taxonomy] = {
                    COUNT_LABEL: 1,
                    NAME_LABEL: collection.original_species_name,
                    HIGHLIGHTER_LABEL: collection.original_species_name,
                    COLLECTION_IDS: [
                        collection.pk
                    ]
                }
            else:
                if collection.pk not in taxon_results[collection.taxonomy][
                    COLLECTION_IDS]:
                    taxon_results[collection.taxonomy][COUNT_LABEL] += 1
                    taxon_results[collection.taxonomy][
                        COLLECTION_IDS].append(collection.pk)

            if collection.location_site_id not in site_results:
                site_results[collection.location_site_id] = {
                    COUNT_LABEL: 1,
                    NAME_LABEL: collection.location_site_name,
                    COLLECTION_IDS: [
                        collection.pk
                    ]
                }
            else:
                if collection.pk not in site_results[
                    collection.location_site_id][COLLECTION_IDS]:
                    site_results[collection.location_site_id][
                        COUNT_LABEL] += 1
                    site_results[collection.location_site_id][
                        COLLECTION_IDS].append(
                            collection.pk)
        return taxon_results, site_results

    @staticmethod
    def process_sites_search(sites, site_results, query):
        for site in sites:
            if site.location_site_id not in site_results:
                site_results[site.location_site_id] = {
                    COUNT_LABEL: 0,
                    NAME_LABEL: site.location_site_name
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
