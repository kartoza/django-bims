from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from bims.api_views.search import MAX_PAGINATED_RECORDS
from bims.models.search_process import SearchProcess


class TaxaSearchResult(APIView):
    """
      Get the paginated taxa data from search results
    """
    def error(self, message):
        return Response({
            'status': 'error',
            'message': message
        })

    def get(self, request):
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
        process_id = request.GET.get('process_id', None)

        if not process_id:
            return self.error('No process ID')

        try:
            search_process = SearchProcess.objects.get(process_id=process_id)
        except SearchProcess.DoesNotExist:
            return self.error('SearchProcess.DoesNotExist')

        if not search_process.finished:
            return self.error('Process not finished yet')

        results = search_process.get_file_if_exits()
        if not results:
            return self.error('Results not found')

        try:
            taxa_results = results['records']
        except KeyError:
            return self.error('File format error')

        taxa_result_paginator = Paginator(taxa_results, MAX_PAGINATED_RECORDS)
        try:
            taxa_result_page = taxa_result_paginator.page(page)
        except (EmptyPage, PageNotAnInteger) as e:
            return self.error(e.message)

        return Response({
            'has_next': taxa_result_page.has_next(),
            'current_page': int(page),
            'num_pages': taxa_result_paginator.num_pages,
            'data': taxa_result_page.object_list
        })
