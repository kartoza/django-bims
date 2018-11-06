# coding=utf-8
from braces.views import LoginRequiredMixin
from django.views.generic import ListView
from bims.models.biological_collection_record import BiologicalCollectionRecord


class NonValidatedObjectsUserView(LoginRequiredMixin, ListView):

    model = BiologicalCollectionRecord
    context_object_name = 'biorecords'
    template_name = 'non_validated_user_list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        filter_name = self.request.GET.get('original_species_name', None)
        filter_date_to = self.request.GET.get('date_to', None)
        filter_date_from = self.request.GET.get('date_from', None)
        context = super(
            NonValidatedObjectsUserView, self).get_context_data(**kwargs)

        # Parameters to be added in the url to update filters.
        # original_species_name filters objects based on its
        # original species name.
        # date_from and date_to filter objects based on its collection date.
        context['custom_url'] = ''
        if filter_name:
            context['custom_url'] = \
                '&original_species_name={}'.format(filter_name)
        if filter_date_from:
            context['custom_url'] = \
                '&date_from={}'.format(filter_date_from)
        if filter_date_to:
            context['custom_url'] += \
                '&date_to={}'.format(filter_date_to)
        return context

    def get_queryset(self):
        filter_name = self.request.GET.get('original_species_name', None)
        filter_date_to = self.request.GET.get('date_to', None)
        filter_date_from = self.request.GET.get('date_from', None)
        user = self.request.user
        if self.queryset is None:
            queryset = \
                BiologicalCollectionRecord.objects.filter(
                    validated=False,
                    owner=user,
                    taxon_gbif_id__isnull=False
                ).order_by('original_species_name')
            if filter_name is not None:
                queryset = queryset.filter(
                    original_species_name__icontains=filter_name)
            if filter_date_from is not None:
                queryset = queryset.filter(
                    collection_date__gte=filter_date_from)
            if filter_date_to is not None:
                queryset = queryset.filter(
                    collection_date__lte=filter_date_to)
            return queryset
        return self.queryset
