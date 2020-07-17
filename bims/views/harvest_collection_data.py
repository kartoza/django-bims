# coding=utf-8
"""Collections uploader view
"""

import os
from collections import deque
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.conf import settings
from django.core.files import File
from bims.models.harvest_session import HarvestSession
from bims.models.taxon_group import TaxonGroup
from bims.tasks.harvest_collections import harvest_collections


class HarvestCollectionView(
    UserPassesTestMixin, LoginRequiredMixin, TemplateView):
    """Generic data upload view."""
    template_name = 'harvest_collection.html'
    category = 'gbif'

    def test_func(self):
        return self.request.user.has_perm('bims.can_upload_data')

    def get_context_data(self, **kwargs):
        context = super(
            HarvestCollectionView, self).get_context_data(**kwargs)
        taxa_upload_sessions = HarvestSession.objects.filter(
            harvester=self.request.user,
            finished=False,
            log_file__isnull=False,
            category=self.category
        )

        if taxa_upload_sessions:
            taxa_upload_session = taxa_upload_sessions[0]
            session_data = {
                'module_group': taxa_upload_session.module_group,
                'finished': taxa_upload_session.finished,
                'start_time': str(taxa_upload_session.start_time),
                'status': taxa_upload_session.status,
                'id': taxa_upload_session.id
            }
            try:
                with open(taxa_upload_session.log_file.path, 'rb') as f:
                    session_data['log'] = b''.join(
                        list(deque(f, 50))).decode('utf-8')
            except ValueError:
                pass
            context['upload_session'] = session_data

        context['finished_sessions'] = HarvestSession.objects.filter(
            harvester=self.request.user,
            finished=True,
            category=self.category
        ).order_by(
            '-start_time'
        )
        context['taxa_groups'] = TaxonGroup.objects.filter(
            category='SPECIES_MODULE'
        ).order_by('display_order')
        return context

    def post(self, request, *args, **kwargs):
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
            return HttpResponseRedirect(request.path_info)
        harvest_session = HarvestSession.objects.create(
            harvester=request.user,
            start_time=datetime.now(),
            module_group_id=taxon_group_id,
            category=self.category
        )
        log_file_folder = os.path.join(
            settings.MEDIA_ROOT, 'harvest-session-log'
        )

        log_file_path = os.path.join(
            log_file_folder, '{id}-{time}.txt'.format(
                id=harvest_session.id,
                time=harvest_session.start_time.strftime('%s')
            )
        )

        if not os.path.exists(log_file_folder):
            os.mkdir(log_file_folder)

        with open(log_file_path, 'a+') as fi:
            harvest_session.log_file = File(fi, name=os.path.basename(fi.name))
            harvest_session.save()

        harvest_collections.delay(harvest_session.id)
        return HttpResponseRedirect(request.path_info)


class HarvestSessionStatusView(APIView):
    """
    Return status of the harvest session
    """

    def get(self, request, session_id, *args):
        try:
            session = HarvestSession.objects.get(
                id=session_id
            )
        except HarvestSession.DoesNotExist:
            raise Http404('No session found')
        session_data = {
            'module_group': session.module_group.name,
            'finished': session.finished,
            'start_time': str(session.start_time),
            'status': session.status
        }
        with open(session.log_file.path, 'rb') as f:
            session_data['log'] = b''.join(
                list(deque(f, 50))).decode('utf-8')
        return Response(session_data)
