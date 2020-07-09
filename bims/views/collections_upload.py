# coding=utf-8
"""Collections uploader view
"""

from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from bims.models.upload_session import UploadSession
from bims.models.taxon_group import TaxonGroup
from bims.tasks.taxa_upload import taxa_upload


class CollectionsUploadView(
    UserPassesTestMixin, LoginRequiredMixin, TemplateView):
    """Taxa upload view."""
    template_name = 'collections_uploader.html'

    def test_func(self):
        return self.request.user.has_perm('bims.can_upload_collection')

    def get_context_data(self, **kwargs):
        context = super(
            CollectionsUploadView, self).get_context_data(**kwargs)
        taxa_upload_sessions = UploadSession.objects.filter(
            uploader=self.request.user,
            processed=False,
            process_file__isnull=False,
            category='collections'
        )
        context['upload_sessions'] = taxa_upload_sessions
        context['finished_sessions'] = UploadSession.objects.filter(
            uploader=self.request.user,
            processed=True,
            category='collections'
        ).order_by(
            '-uploaded_at'
        )
        context['taxa_groups'] = TaxonGroup.objects.filter(
            category='SPECIES_MODULE'
        ).order_by('display_order')
        return context

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        taxon_group_id = request.POST.get('taxon_group', None)
        taxon_group_logo = request.FILES.get('taxon_group_logo')
        taxon_group_name = request.POST.get('taxon_group_name', '')
        if taxon_group_logo and taxon_group_logo:
            taxon_groups = TaxonGroup.objects.filter(
                category='SPECIES_MODULE'
            ).order_by('-display_order')
            display_order = 1
            if taxon_groups:
                display_order = taxon_groups[0].display_order + 1
            TaxonGroup.objects.create(
                name=taxon_group_name,
                logo=taxon_group_logo,
                category='SPECIES_MODULE',
                display_order=display_order
            )
            return HttpResponseRedirect('/upload-taxa')
        if not csv_file:
            raise Http404('Missing csv file')
        upload_session = UploadSession.objects.create(
            uploader=request.user,
            process_file=csv_file,
            uploaded_at=datetime.now(),
            module_group_id=taxon_group_id,
            category='collections'
        )
        taxa_upload.delay(upload_session.id)
        return HttpResponseRedirect('/upload-taxa')


class CollectionsUploadStatusView(APIView):
    """
    Return status of the collections upload
    """

    def get(self, request, session_id, *args):
        try:
            session = UploadSession.objects.get(
                id=session_id
            )
        except UploadSession.DoesNotExist:
            raise Http404('No session found')
        return Response({
            'token': session.token,
            'progress': session.progress,
            'processed': session.processed
        })
