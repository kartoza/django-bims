from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from bims.api_views.search_version_2 import MAX_PAGINATED_SITES
from bims.models.search_process import SearchProcess


class SiteSearchResult(APIView):
    """
    Get the paginated site data from search results
    """
    def error(self, message):
        return Response({
            'status': 'error',
            'message': message
        })

    def get(self, request):
        page = request.GET.get('page', 1)
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
            site_results = results['sites']
        except KeyError:
            return self.error('File format error')

        site_result_paginator = Paginator(site_results, MAX_PAGINATED_SITES)
        try:
            site_result_page = site_result_paginator.page(page)
        except (EmptyPage, PageNotAnInteger) as e:
            return self.error(e.message)

        return Response({
            'has_next': site_result_page.has_next(),
            'current_page': int(page),
            'num_pages': site_result_paginator.num_pages,
            'data': site_result_page.object_list
        })
