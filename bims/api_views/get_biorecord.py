# coding=utf-8
import json
import os
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response
from django.http import HttpResponse
from django.db.models import Count, F
from django.db.models.functions import ExtractYear
from rest_framework import status
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.iucn_status import IUCNStatus
from bims.serializers.bio_collection_serializer import (
    BioCollectionSerializer,
    BioCollectionDetailSerializer,
)
from bims.utils.search_process import (
    get_or_create_search_process,
    create_search_process_file
)
from bims.models.search_process import TAXON_SUMMARY
from bims.api_views.search_version_2 import SearchVersion2


class GetBioRecordDetail(LoginRequiredMixin, APIView):

    def get(self, request):
        object_pk = request.GET.get('pk', None)
        try:
            object = BiologicalCollectionRecord.objects.get(pk=object_pk)
            serializer = BioCollectionDetailSerializer(object)
            return Response(serializer.data)
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )


class GetBioRecords(APIView):

    def get(self, request):
        filters = request.GET
        search = SearchVersion2(filters)

        # Search collection
        collection_results = search.process_search()

        try:
            serializer = BioCollectionSerializer(
                collection_results,
                many=True)
            return Response(serializer.data)
        except BiologicalCollectionRecord.DoesNotExist:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )


class BioCollectionSummary(APIView):
    """Api to get biological collection summary data"""

    def get(self, request):
        filters = request.GET
        search = SearchVersion2(filters)

        search_process, created = get_or_create_search_process(
            TAXON_SUMMARY,
            query=request.build_absolute_uri()
        )

        if search_process.file_path:
            if os.path.exists(search_process.file_path):
                try:
                    raw_data = open(search_process.file_path)
                    return Response(json.load(raw_data))
                except ValueError:
                    pass

        collection_results = search.process_search()
        response_data = {}

        if not collection_results:
            return HttpResponse(
                'Object Does Not Exist',
                status=status.HTTP_400_BAD_REQUEST
            )
        records_over_time = collection_results.annotate(
            year=ExtractYear('collection_date')).values('year').annotate(
            count=Count('year')).order_by('year')
        records_per_area = collection_results.annotate(
            site_name=F('site__name')
        ).values('site_name').annotate(
            count=Count('site_name'),
            site_code=F('site__site_code'),
            site_id=F('site__id'),
            river=F('site__river__name')
        )

        taxonomy = collection_results[0].taxonomy

        search_process.set_search_raw_query(search.location_sites_raw_query)
        search_process.create_view()
        endemic = None
        if taxonomy.endemism:
            endemic = taxonomy.endemism.name
        iucn_status = None
        if taxonomy.iucn_status:
            iucn_status = taxonomy.iucn_status.category
        response_data['iucn_id'] = taxonomy.iucn_redlist_id
        response_data['taxon'] = taxonomy.scientific_name
        response_data['gbif_id'] = taxonomy.gbif_key
        response_data['total_records'] = len(collection_results)
        response_data['conservation_status'] = iucn_status
        response_data['origin'] = collection_results[0].category
        response_data['endemism'] = endemic
        response_data['records_over_time_labels'] = (
            list(records_over_time.values_list('year', flat=True))
        )
        response_data['records_over_time_data'] = (
            list(records_over_time.values_list('count', flat=True))
        )
        response_data['records_per_area'] = list(records_per_area)
        response_data['sites_raw_query'] = search_process.process_id
        response_data['process_id'] = search_process.process_id
        response_data['extent'] = search.extent()
        response_data['origin_choices_list'] = (
            BiologicalCollectionRecord.CATEGORY_CHOICES)
        response_data['iucn_choice_list'] = IUCNStatus.CATEGORY_CHOICES

        taxonomy_rank = {
            taxonomy.rank: taxonomy.scientific_name
        }
        taxonomy_parent = taxonomy.parent
        while taxonomy_parent:
            taxonomy_rank[taxonomy_parent.rank] = (
                taxonomy_parent.canonical_name
            )
            taxonomy_parent = taxonomy_parent.parent
        response_data['taxonomy_rank'] = taxonomy_rank

        common_names = []
        # Common name
        if taxonomy.vernacular_names.filter(language='eng').exists():
            common_names = list(
                taxonomy.vernacular_names.all().filter(language='eng').values()
            )
        elif taxonomy.vernacular_names.all().values().exists():
            common_names = list(taxonomy.vernacular_names.all().values())
        if len(common_names) == 0:
            response_data['common_name'] = 'Unknown'
        else:
            response_data['common_name'] = str(
                common_names[0]['name']).capitalize()
        file_path = create_search_process_file(
            data=response_data,
            search_process=search_process,
            finished=True
        )
        file_data = open(file_path)

        try:
            return Response(json.load(file_data))
        except ValueError:
            return Response(response_data)
