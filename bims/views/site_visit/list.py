from django.views.generic.list import ListView
from bims.models.survey import Survey
from bims.api_views.search import Search


class SiteVisitListView(ListView):
    model = Survey
    paginate_by = 20
    template_name = 'site_visit/site_visit_list.html'

    def get_queryset(self):
        """
        Add GET requests filters
        """
        search_filters = self.request.GET.dict()

        # Remove page in filters
        if 'page' in search_filters:
            del search_filters['page']

        # Base queryset
        qs = super(SiteVisitListView, self).get_queryset()

        if search_filters:
            search = Search(search_filters)
            collection_results = search.process_search()
            qs = qs.filter(
                id__in=collection_results.values('survey')
            )

        return qs.order_by('-date')
