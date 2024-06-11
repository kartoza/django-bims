import json
import ast

from django.contrib.sites.models import Site
from django.views.generic.list import ListView
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.db.models import Subquery, OuterRef
from bims.models.survey import Survey
from bims.enums.ecosystem_type import (
    ECOSYSTEM_RIVER,
    ECOSYSTEM_WETLAND,
    ECOSYSTEM_OPEN_WATERBODY,
    ECOSYSTEM_UNSPECIFIED
)
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.taxon_group import TaxonGroup, TaxonomicGroupCategory
from bims.api_views.search import CollectionSearch


class SiteVisitListView(ListView):
    model = Survey
    paginate_by = 20
    template_name = 'site_visit/site_visit_list.html'
    collection_results = BiologicalCollectionRecord.objects.none()

    def check_filters(self, search_filters):
        if 'o' in search_filters:
            del search_filters['o']
        if 'validated' in search_filters:
            return True

    def get_queryset(self):
        """
        Add GET requests filters
        """
        search_filters = self.request.GET.dict()
        order = '-date'

        # Remove page in filters
        if 'page' in search_filters:
            del search_filters['page']

        if 'o' in search_filters:
            order = search_filters['o']
            del search_filters['o']

        # Base queryset
        qs = super(SiteVisitListView, self).get_queryset().all()

        if search_filters:
            search = CollectionSearch(search_filters)

            if 'site_code' in search_filters:
                if search_filters['site_code']:
                    qs = qs.filter(
                        site__site_code=search_filters['site_code']
                    )
                del search_filters['site_code']
            if 'collectors' in search_filters:
                if search_filters['collectors']:
                    qs = qs.filter(
                        owner__in=search.collectors
                    )
                del search_filters['collectors']
            if 'validated' in search_filters:
                validation_filters = search.validation_filter()
                if validation_filters:
                    validation_filter = {}
                    for validation_key in validation_filters:
                        validation_filter[
                            validation_key.replace('survey__', '')
                        ] = validation_filters[validation_key]
                    qs = qs.filter(
                        **validation_filter
                    )
                del search_filters['validated']

            if search_filters:
                search = CollectionSearch(search_filters)
                self.collection_results = search.process_search()
                qs = qs.filter(
                    id__in=self.collection_results.values('survey')
                )
        else:
            self.collection_results = BiologicalCollectionRecord.objects.filter(
                source_site=Site.objects.get_current()
            )

        qs = qs.annotate(
            total=Count('biological_collection_record'),
            source_collection=Subquery(
                BiologicalCollectionRecord.objects.filter(
                    survey__id=OuterRef('id')
                ).values('source_collection')[:1])
        )
        return qs.order_by(order, 'id')

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

        if self.request.GET.get('site_code'):
            context['site_code'] = self.request.GET.get('site_code')

        # Get source collection if exist in request
        try:
            context['source_collection'] = ast.literal_eval(
                self.request.GET.get('sourceCollection', '[]')
            )
        except SyntaxError:
            context['source_collection'] = []

        # Module
        context['modules'] = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )
        selected_module = self.request.GET.get('modules', '')
        if selected_module:
            context['selected_module'] = int(selected_module)

        context['total_sites'] = total_sites
        context['total_records'] = total_records
        context['collector_owner'] = collector_owner

        return context
