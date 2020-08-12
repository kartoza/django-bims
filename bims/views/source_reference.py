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
    paginate_by = 20
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

        return super(SourceReferenceListView, self).get(
            request, *args, **kwargs)

    def get_queryset(self):
        """
        Add GET requests filters
        """
        filters = dict()
        # Base queryset
        qs = super(SourceReferenceListView, self).get_queryset()

        if self.type_filter:
            or_condition = Q()
            type_filters = self.type_filter.split(',')
            for type_filter in type_filters:
                if type_filter in self.source_reference_type:
                    or_condition |= Q(**{
                        'instance_of':
                        self.source_reference_type[type_filter
                    ]})
            qs = qs.filter(or_condition)

        qs = qs.filter(**filters)

        # Return filtered queryset
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = [
            {
                'title': 'Unpublished',
                'count': SourceReference.objects.exclude(
                    Q(instance_of=SourceReferenceDatabase) |
                    Q(instance_of=SourceReferenceDocument) |
                    Q(instance_of=SourceReferenceBibliography)
                ).count(),
                'key': 'unpublished',
                'selected': 'unpublished' in self.type_filter
            },
            {
                'title': 'Database',
                'count': SourceReference.objects.instance_of(
                    SourceReferenceDatabase
                ).count(),
                'key': 'database',
                'selected': 'database' in self.type_filter
            },
            {
                'title': 'Published report or thesis',
                'count': SourceReference.objects.instance_of(
                    SourceReferenceDocument
                ).count(),
                'key': 'document',
                'selected': 'document' in self.type_filter
            },
            {
                'title': 'Peer-reviewed scientific article',
                'count': SourceReference.objects.instance_of(
                    SourceReferenceBibliography
                ).count(),
                'key': 'bibliography',
                'selected': 'bibliography' in self.type_filter
            }
        ]
        return context

