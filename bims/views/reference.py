from django.views.generic import ListView
from django.db.models import Q
from bims.models.source_reference import SourceReference


class ReferenceListView(ListView):
    model = SourceReference
    paginate_by = 20
    template_name = 'source_references/reference_list.html'

    def get(self, request, *args, **kwargs):
        """Check GET request parameters validity and store them"""

        # -- Search query
        search = self.request.GET.get('q', None)
        if search:
            self.query_search = search
        else:
            self.query_search = ''
        return super(ReferenceListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Add GET requests filters
        """
        filters = dict()

        # Base queryset
        qs = super(ReferenceListView, self).get_queryset()
        qs = qs.filter(**filters)

        # Query search
        if self.query_search:
            qs = qs.filter(
                Q(sourcereferencebibliography__source__title__icontains=
                  self.query_search) |
                Q(sourcereferencedatabase__source__name__icontains=
                  self.query_search) |
                Q(sourcereferencedocument__source__title__icontains=
                  self.query_search)
            )

        # Return filtered queryset
        return qs
