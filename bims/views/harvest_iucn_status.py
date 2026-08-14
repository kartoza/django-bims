# coding=utf-8
import os

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.files import File
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from bims.models.harvest_session import HarvestSession
from bims.tasks.taxa import fetch_iucn_status


class HarvestIUCNStatusView(
    UserPassesTestMixin,
    LoginRequiredMixin,
    TemplateView,
):
    template_name = 'harvest_iucn_status.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        active_session = (
            HarvestSession.objects.filter(
                category='iucn',
                finished=False,
                canceled=False,
            )
            .order_by('-start_time')
            .first()
        )
        ctx['active_session'] = active_session

        if active_session and active_session.log_file and active_session.log_file.name:
            from collections import deque
            try:
                with open(active_session.log_file.path, 'rb') as f:
                    ctx['active_session_log'] = b''.join(
                        list(deque(f, 50))
                    ).decode('utf-8')
            except (OSError, ValueError):
                ctx['active_session_log'] = ''
        else:
            ctx['active_session_log'] = ''

        ctx['finished_sessions'] = (
            HarvestSession.objects.filter(
                category='iucn',
            )
            .exclude(finished=False, canceled=False)
            .order_by('-start_time')[:20]
        )
        return ctx

    def post(self, request, *args, **kwargs):
        if request.POST.get('cancel', '').lower() == 'true':
            session_id = request.POST.get('canceled_session_id', '')
            try:
                session = HarvestSession.objects.get(
                    id=int(session_id),
                    category='iucn',
                )
                session.canceled = True
                session.save()
            except (HarvestSession.DoesNotExist, ValueError):
                pass
            return HttpResponseRedirect(request.path_info)

        active = HarvestSession.objects.filter(
            category='iucn',
            finished=False,
            canceled=False,
        ).exists()

        if not active:
            session = HarvestSession.objects.create(
                harvester=request.user,
                category='iucn',
                status='queued',
            )

            log_folder = os.path.join(settings.MEDIA_ROOT, 'harvest-session-log')
            os.makedirs(log_folder, exist_ok=True)
            log_path = os.path.join(
                log_folder,
                'iucn-{id}-{ts}.txt'.format(
                    id=session.id,
                    ts=session.start_time.strftime('%s'),
                )
            )
            with open(log_path, 'a+') as f:
                session.log_file = File(f, name=os.path.basename(f.name))
                session.save()

            fetch_iucn_status.delay(session_id=session.id)

        return HttpResponseRedirect(request.path_info)
