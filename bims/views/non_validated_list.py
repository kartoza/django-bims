# coding=utf-8
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.permissions.api_permission import (
    user_has_permission_to_validate,
    AllowedTaxon,
)


class NonValidatedObjectsView(
        UserPassesTestMixin,
        LoginRequiredMixin,
        ListView):

    model = BiologicalCollectionRecord
    context_object_name = 'biorecords'
    template_name = 'non_validated_list.html'
    paginate_by = 10

    def test_func(self):
        return user_has_permission_to_validate(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, 'You don\'t have permission '
                                     'to validate collection data')
        return super(NonValidatedObjectsView, self).handle_no_permission()

    def get_context_data(self, **kwargs):
        filter_name = self.request.GET.get('original_species_name', None)
        filter_owner = self.request.GET.get('owner', None)
        filter_date_to = self.request.GET.get('date_to', None)
        filter_date_from = self.request.GET.get('date_from', None)
        context = super(
            NonValidatedObjectsView, self).get_context_data(**kwargs)
        context['custom_url'] = ''
        if filter_name:
            context['custom_url'] = \
                '&original_species_name={}'.format(filter_name)
        elif filter_owner:
            context['custom_url'] = \
                '&owner={}'.format(filter_owner)

        if filter_date_from:
            context['custom_url'] = \
                '&date_from={}'.format(filter_date_from)
        if filter_date_to:
            context['custom_url'] += \
                '&date_to={}'.format(filter_date_to)
        return context

    def get_queryset(self):
        filter_name = self.request.GET.get('original_species_name', None)
        filter_owner = self.request.GET.get('owner', None)
        filter_date_to = self.request.GET.get('date_to', None)
        filter_date_from = self.request.GET.get('date_from', None)
        filter_pk = self.request.GET.get('pk', None)
        if self.queryset is None:
            allowed_taxon = AllowedTaxon().get(self.request.user)
            queryset = \
                BiologicalCollectionRecord.objects.filter(
                    taxon_gbif_id__in=allowed_taxon,
                    ready_for_validation=True,
                    validated=False).order_by('original_species_name')
            if filter_pk is not None:
                queryset = queryset.filter(pk=filter_pk)
            if filter_name is not None:
                queryset = queryset.filter(
                    original_species_name__icontains=filter_name)
            if filter_owner is not None:
                queryset = queryset.filter(
                    owner__username__icontains=filter_owner)
            if filter_date_from is not None:
                queryset = queryset.filter(
                    collection_date__gte=filter_date_from)
            if filter_date_to is not None:
                queryset = queryset.filter(
                    collection_date__lte=filter_date_to)
            return queryset
        return self.queryset
