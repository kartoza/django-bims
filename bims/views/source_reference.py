from django.views.generic import ListView
from django.db.models import Q
from bims.models.source_reference import (
    SourceReference,
    SourceReferenceBibliography,
    SourceReferenceDatabase,
    SourceReferenceDocument
)


class SourceReferenceListView(ListView):
    model = SourceReference
    template_name = 'source_reference_list.html'
    paginate_by = 15
    source_reference_type = {
        'database': SourceReferenceDatabase,
        'bibliography': SourceReferenceBibliography,
        'document': SourceReferenceDocument
    }

    def get(self, request, *args, **kwargs):
        """Check GET request parameters validity and store them"""
        # -- Type query
        source_reference_type = self.request.GET.get('type', None)
        if source_reference_type:
            self.type_filter = source_reference_type
        else:
            self.type_filter = ''

        # -- Search query
        self.search_query = self.request.GET.get('q', '')

        # -- Collectors
        self.collectors = self.request.GET.get('collectors', None)
        if self.collectors:
            self.collectors = self.collectors.split(',')

        return super(SourceReferenceListView, self).get(
            request, *args, **kwargs)

    def get_queryset(self):
        """
        Add GET requests filters
        """
        filters = dict()
        # Base queryset
        qs = super(SourceReferenceListView, self).get_queryset()

        if self.collectors:
            qs = qs.filter(
                Q(sourcereferencebibliography__source__authors__user__in=
                  self.collectors) |
                Q(sourcereferencebibliography__document__bimsdocument__authors__in=  # noqa
                  self.collectors) |
                Q(sourcereferencedocument__source__bimsdocument__authors__in=
                  self.collectors) |
                Q(sourcereferencedocument__source__owner__in=self.collectors)
            )

        if self.type_filter:
            or_condition = Q()
            type_filters = self.type_filter.split(',')
            for type_filter in type_filters:
                if type_filter in self.source_reference_type:
                    or_condition |= Q(**{
                        'instance_of':
                            self.source_reference_type[type_filter]
                    })
                else:
                    for source_reference_type in self.source_reference_type:
                        or_condition &= Q(**{
                            'not_instance_of':
                                self.source_reference_type[
                                    source_reference_type]})
            qs = qs.filter(or_condition)

        if self.search_query:
            qs = qs.filter(
                Q(sourcereferencebibliography__source__title__icontains =
                  self.search_query) |
                Q(sourcereferencedocument__source__title__icontains =
                  self.search_query) |
                Q(sourcereferencedatabase__source__name__icontains =
                  self.search_query) |
                Q(note__icontains = self.search_query) |
                Q(source_name__icontains = self.search_query)
            )

        qs = qs.filter(**filters)

        # Return filtered queryset
        return qs

    def get_context_data(self, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.get_queryset()
        context['type'] = [
            {
                'title': 'Unpublished',
                'count': data.exclude(
                    Q(instance_of=SourceReferenceDatabase) |
                    Q(instance_of=SourceReferenceDocument) |
                    Q(instance_of=SourceReferenceBibliography)
                ).count(),
                'key': 'unpublished',
                'selected': 'unpublished' in self.type_filter
            },
            {
                'title': 'Database',
                'count': data.instance_of(
                    SourceReferenceDatabase
                ).count(),
                'key': 'database',
                'selected': 'database' in self.type_filter
            },
            {
                'title': 'Published report or thesis',
                'count': data.instance_of(
                    SourceReferenceDocument
                ).count(),
                'key': 'document',
                'selected': 'document' in self.type_filter
            },
            {
                'title': 'Peer-reviewed scientific article',
                'count': data.instance_of(
                    SourceReferenceBibliography
                ).count(),
                'key': 'bibliography',
                'selected': 'bibliography' in self.type_filter
            }
        ]
        context['search'] = self.search_query
        return context
