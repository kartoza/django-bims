import json
from django.views.generic.list import ListView
from django.db.models import Count
from django.contrib.auth import get_user_model
from bims.models.survey import Survey
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.api_views.search import CollectionSearch


class SiteVisitListView(ListView):
    model = Survey
    paginate_by = 20
    template_name = 'site_visit/site_visit_list.html'
    collection_results = BiologicalCollectionRecord.objects.none()

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
            search = CollectionSearch(search_filters)
            self.collection_results = search.process_search()
            qs = qs.filter(
                id__in=self.collection_results.values('survey')
            ).annotate(
                total=Count('biological_collection_record')
            )

        return qs.order_by('-date')

    def get_context_data(self, **kwargs):
        """
        Get context data which is passed to a template
        """
        context = super(SiteVisitListView, self).get_context_data(**kwargs)

        # - Total sites
        total_sites = (
            self.collection_results.values('site').distinct('site').count()
        )

        # - Total collection records
        total_records = self.collection_results.count()

        # - Get owner object from the id passed from the request
        collector_owner = None
        if self.request.GET.get('collectors'):
            try:
                ids = json.loads(self.request.GET.get('collectors'))
                user_model = get_user_model()
                collector_owner = user_model.objects.filter(
                    id__in=ids
                )
            except ValueError:
                # Couldn't parse the ids
                pass

        context['total_sites'] = total_sites
        context['total_records'] = total_records
        context['collector_owner'] = collector_owner

        return context
