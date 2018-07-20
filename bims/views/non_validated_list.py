# coding=utf-8
from braces.views import LoginRequiredMixin
from django.views.generic import ListView
from bims.models.biological_collection_record import BiologicalCollectionRecord


class NonValidatedObjectsView(LoginRequiredMixin, ListView):

    model = BiologicalCollectionRecord
    context_object_name = 'biorecords'
    template_name = 'non_validated_list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(
            NonValidatedObjectsView, self).get_context_data(**kwargs)
        return context

    def get_queryset(self):
        if self.queryset is None:
            queryset = \
                BiologicalCollectionRecord.objects.filter(
                    validated=False).order_by('original_species_name')
            return queryset
        return self.queryset
