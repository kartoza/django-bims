# coding=utf-8
"""Collections uploader view
"""

import ast
import os
from datetime import datetime

import pandas as pd
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, Http404
from django.db.models import Q
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from bims.models.upload_session import UploadSession
from bims.models.taxon_group import TaxonGroup


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
                display_order = taxon_groups[0].display_order + 1
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
                excel_data = pd.read_excel(upload_file)
                with NamedTemporaryFile(delete=False, suffix=".csv") as temp_csv_file:
                    csv_file_path = temp_csv_file.name
                    excel_data.to_csv(csv_file_path, index=False)

                    with open(csv_file_path, 'rb') as csv_file:
                        csv_content = ContentFile(csv_file.read())
                    csv_file_name = f"{os.path.splitext(upload_file.name)[0]}.csv"
                    upload_session = UploadSession.objects.create(
                        uploader=request.user,
                        uploaded_at=datetime.now(),
                        module_group_id=taxon_group_id,
                        category=self.category
                    )
                    upload_session.process_file.save(csv_file_name, csv_content)
            elif file_extension == '.csv':
                upload_session = UploadSession.objects.create(
                    uploader=request.user,
                    process_file=upload_file,
                    uploaded_at=datetime.now(),
                    module_group_id=taxon_group_id,
                    category=self.category
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
    Return status of the data upload
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
            'processed': session.processed,
            'canceled': session.canceled
        })
