import ast
import os
from collections import deque
from datetime import datetime

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.core.files import File
from bims.models.taxon_group import TaxonGroup
from bims.models.boundary import Boundary
from bims.models.harvest_session import HarvestSession
from bims.tasks.harvest_gbif_species import harvest_gbif_species


class HarvestGbifSpeciesView(
    UserPassesTestMixin,
    LoginRequiredMixin,
    TemplateView
):
    template_name = 'harvest_gbif_species.html'

    def test_func(self):
        return self.request.user.has_perm('bims.can_harvest_species')

    def get_context_data(self, **kwargs):
        ctx = super(
            HarvestGbifSpeciesView, self).get_context_data(**kwargs)

        ctx['boundaries'] = Boundary.objects.filter(
            geometry__isnull=False
        ).order_by('-id')
        ctx['taxa_groups'] = TaxonGroup.objects.filter(
            category='SPECIES_MODULE',
        ).order_by('display_order')

        harvest_sessions = HarvestSession.objects.filter(
            harvester=self.request.user,
            finished=False,
            canceled=False,
            log_file__isnull=False,
            is_fetching_species=True
        )

        if harvest_sessions:
            harvest_session = harvest_sessions[0]
            session_data = {
                'module_group': harvest_session.module_group,
                'finished': harvest_session.finished,
                'start_time': str(harvest_session.start_time),
                'status': harvest_session.status,
                'id': harvest_session.id
            }
            try:
                with open(harvest_session.log_file.path, 'rb') as f:
                    session_data['log'] = b''.join(
                        list(deque(f, 50))).decode('utf-8')
            except ValueError:
                pass
            ctx['upload_session'] = session_data

        ctx['finished_sessions'] = HarvestSession.objects.filter(
            Q(finished=True) | Q(canceled=True),
            harvester=self.request.user,
            is_fetching_species=True,
        ).order_by(
            '-start_time'
        )
        return ctx

    def post(self, request, *args, **kwargs):
        taxon_group_id = request.POST.get('taxon_group', None)
        taxon_group_logo = request.FILES.get('taxon_group_logo')
        taxon_group_name = request.POST.get('taxon_group_name', '')
        boundary_id = request.POST.get('boundary', None)
        cancel = ast.literal_eval(request.POST.get(
            'cancel', 'False'
        ))
        if cancel:
            session_id = request.POST.get('canceled_session_id', '')
            try:
                harvest_session = HarvestSession.objects.get(
                    id=int(session_id)
                )
                harvest_session.canceled = True
                harvest_session.save()
                return HttpResponseRedirect(request.path_info)
            except (HarvestSession.DoesNotExist, ValueError):
                pass
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
            category='gbif',
            boundary_id=boundary_id,
            is_fetching_species=True
        )
        log_file_folder = os.path.join(
            settings.MEDIA_ROOT, 'harvest-species-session-log'
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

        harvest_gbif_species.delay(harvest_session.id)
        return HttpResponseRedirect(request.path_info)
