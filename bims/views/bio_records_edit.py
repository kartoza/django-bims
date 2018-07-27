# coding=utf-8
from braces.views import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from bims.models import BiologicalCollectionRecord


class BioRecordsUpdateView(LoginRequiredMixin, UpdateView):
    model = BiologicalCollectionRecord
    template_name = 'bio_records_update.html'
    fields = [
        'site',
        'original_species_name',
        'category',
        'present',
        'absent',
        'collection_date',
        'notes',
        'taxon_gbif_id'
    ]
    success_url = reverse_lazy('nonvalidated-user-list')

    def user_passes_test(self, request):
        if request.user.is_authenticated():
            self.object = self.get_object()
            return self.object.owner == request.user
        return False

    def dispatch(self, request, *args, **kwargs):
        if not self.user_passes_test(request):
            raise PermissionDenied
        return super(BioRecordsUpdateView, self).dispatch(
            request, *args, **kwargs)
