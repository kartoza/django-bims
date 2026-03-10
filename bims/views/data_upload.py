# coding=utf-8
"""Collections uploader view
"""

import ast
import os
from datetime import datetime, timedelta

import pandas as pd
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, Http404
from django.db.models import Q
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from bims.models.upload_session import UploadSession
from bims.models.taxon_group import TaxonGroup

# A session is considered stale/stuck when no progress has been recorded
# for this many minutes
STALE_THRESHOLD_MINUTES = 15

RESUMABLE_TASK_MAP = {
    'taxa': 'bims.tasks.taxa_upload',
    'collections': 'bims.tasks.collections_upload',
    'physico_chemical': 'bims.tasks.physico_chemical_upload',
}


class DataUploadView(
    UserPassesTestMixin,
    LoginRequiredMixin,
    TemplateView
):
    """Generic data upload view."""
    template_name = ''
    upload_task = None
    category = ''

    def test_func(self):
        return self.request.user.has_perm('bims.can_upload_data')

    def get_context_data(self, **kwargs):
        context = super(
            DataUploadView, self).get_context_data(**kwargs)
        taxa_upload_sessions = UploadSession.objects.filter(
            uploader=self.request.user,
            processed=False,
            canceled=False,
            process_file__isnull=False,
            category=self.category
        )
        context['upload_sessions'] = taxa_upload_sessions
        context['finished_sessions'] = UploadSession.objects.filter(
            Q(processed=True) | Q(canceled=True),
            uploader=self.request.user,
            category=self.category
        ).order_by(
            '-uploaded_at'
        )
        context['taxa_groups'] = TaxonGroup.objects.filter(
            category='SPECIES_MODULE'
        ).order_by('display_order')
        return context

    def post(self, request, *args, **kwargs):
        upload_file = request.FILES.get('csv_file')
        taxon_group_id = request.POST.get('taxon_group', None)
        taxon_group_logo = request.FILES.get('taxon_group_logo')
        taxon_group_name = request.POST.get('taxon_group_name', '')
        template = request.POST.get('template', '')
        harvest_synonyms = request.POST.get("harvest_synonyms_for_accepted") == "1"

        cancel = ast.literal_eval(request.POST.get(
            'cancel', 'False'
        ))
        if cancel:
            session_id = request.POST.get('canceled_session_id', '')
            try:
                upload_session = UploadSession.objects.get(
                    id=int(session_id)
                )
                upload_session.canceled = True
                upload_session.save()
                return HttpResponseRedirect(request.path_info)
            except (UploadSession.DoesNotExist, ValueError):
                pass
        if taxon_group_logo and taxon_group_logo:
            taxon_groups = TaxonGroup.objects.filter(
                category='SPECIES_MODULE'
            ).order_by('-display_order')
            display_order = 1
            if taxon_groups:
                display_order = len(taxon_groups) + 1
            TaxonGroup.objects.create(
                name=taxon_group_name,
                logo=taxon_group_logo,
                category='SPECIES_MODULE',
                display_order=display_order
            )
            return HttpResponseRedirect(request.path_info)
        if not upload_file:
            raise Http404('Missing file')

        file_extension = os.path.splitext(upload_file.name)[1].lower()

        try:
            if file_extension in ['.xls', '.xlsx']:
                df = pd.read_excel(
                    upload_file,
                    dtype=str,
                    na_values=[''],
                    keep_default_na=False
                )
                # Replace NaN with empty strings
                df = df.fillna('')
                df = df.replace(['nan', '0'], '')

                with NamedTemporaryFile(delete=False, suffix=".csv") as temp_csv_file:
                    csv_file_path = temp_csv_file.name
                    df.to_csv(csv_file_path, index=False)

                    with open(csv_file_path, 'rb') as csv_file:
                        csv_content = ContentFile(csv_file.read())
                    csv_file_name = f"{os.path.splitext(upload_file.name)[0]}.csv"
                    upload_session = UploadSession.objects.create(
                        uploader=request.user,
                        uploaded_at=datetime.now(),
                        module_group_id=taxon_group_id,
                        category=self.category,
                        template=template,
                        harvest_synonyms=harvest_synonyms
                    )
                    upload_session.process_file.save(csv_file_name, csv_content)
            elif file_extension == '.csv':
                upload_session = UploadSession.objects.create(
                    uploader=request.user,
                    process_file=upload_file,
                    uploaded_at=datetime.now(),
                    module_group_id=taxon_group_id,
                    category=self.category,
                    template=template,
                    harvest_synonyms=harvest_synonyms
                )

            else:
                raise Http404('Unsupported file type')

        except Exception as e:
            raise Http404(f'Failed to process file: {str(e)}')
        if self.upload_task:
            self.upload_task.delay(upload_session.id)
        return HttpResponseRedirect(request.path_info)


class DataUploadStatusView(APIView):
    """
    Return status of the data upload.
    Includes `is_stale` flag when the task appears to have stopped,
    and `can_resume` to indicate whether auto-resume is supported.
    """

    def get(self, request, session_id, *args):
        try:
            session = UploadSession.objects.get(id=session_id)
        except UploadSession.DoesNotExist:
            raise Http404('No session found')

        is_stale = False
        if not session.processed and not session.canceled:
            now = timezone.now()
            if session.last_progress_update:
                delta = now - session.last_progress_update
                is_stale = delta > timedelta(minutes=STALE_THRESHOLD_MINUTES)
            elif session.progress:
                # Task started (set progress text) but never reached the row
                # processing loop — check against upload time.
                uploaded_at = session.uploaded_at
                if timezone.is_naive(uploaded_at):
                    uploaded_at = timezone.make_aware(uploaded_at)
                delta = now - uploaded_at
                is_stale = delta > timedelta(minutes=STALE_THRESHOLD_MINUTES * 2)

        return Response({
            'token': str(session.token),
            'progress': session.progress,
            'processed': session.processed,
            'canceled': session.canceled,
            'is_stale': is_stale,
            'can_resume': session.category in RESUMABLE_TASK_MAP,
        })


class ResumeUploadView(APIView):
    """
    Re-queue a stale/stuck upload session so processing continues
    from the last saved checkpoint (upload_session.start_row).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id, *args):
        try:
            session = UploadSession.objects.get(id=session_id)
        except UploadSession.DoesNotExist:
            raise Http404('No session found')

        # Only the uploader or staff may resume.
        if not request.user.is_staff and session.uploader != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=http_status.HTTP_403_FORBIDDEN
            )

        if session.processed or session.canceled:
            return Response(
                {'error': 'Session is already completed or cancelled'},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        task_name = RESUMABLE_TASK_MAP.get(session.category)
        if not task_name:
            return Response(
                {'error': f'Auto-resume is not supported for category: {session.category}'},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        # Reset the stale timestamp so we don't immediately re-trigger resume.
        session.last_progress_update = timezone.now()
        session.save(update_fields=['last_progress_update'])

        from celery import current_app
        current_app.send_task(task_name, args=[session.id])

        return Response({'status': 'resumed', 'session_id': session.id, 'start_row': session.start_row})
