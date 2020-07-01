# coding=utf-8
"""Taxa uploader view
"""

from datetime import datetime
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from bims.models.taxa_upload_session import TaxaUploadSession
from bims.models.taxon_group import TaxonGroup
from bims.tasks.taxa_upload import taxa_upload


class TaxaUploadView(UserPassesTestMixin, LoginRequiredMixin, TemplateView):
    """Taxa upload view."""
    template_name = 'taxa_uploader.html'

    def test_func(self):
        return self.request.user.has_perm('bims.can_upload_taxa')

    def get_context_data(self, **kwargs):
        context = super(TaxaUploadView, self).get_context_data(**kwargs)
        taxa_upload_sessions = TaxaUploadSession.objects.filter(
            uploader=self.request.user,
            processed=False,
            process_file__isnull=False
        )
        context['upload_sessions'] = taxa_upload_sessions
        context['finished_sessions'] = TaxaUploadSession.objects.filter(
            uploader=self.request.user,
            processed=True
        )
        context['taxa_groups'] = TaxonGroup.objects.filter(
            category='SPECIES_MODULE'
        ).order_by('display_order')
        return context

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        taxon_group_id = request.POST.get('taxon_group', None)
        if not csv_file:
            raise Http404('Missing csv file')
        taxa_upload_session = TaxaUploadSession.objects.create(
            uploader=request.user,
            process_file=csv_file,
            uploaded_at=datetime.now(),
            module_group_id=taxon_group_id
        )
        taxa_upload(taxa_upload_session.id)
        return HttpResponseRedirect('/upload-taxa')
