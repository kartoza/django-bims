# coding=utf-8
"""Taxa uploader view
"""
import ast
import os
from datetime import datetime

import pandas as pd
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404

from bims.models.upload_session import UploadSession
from bims.views.data_upload import DataUploadView
from bims.tasks.taxa_upload import taxa_upload
from bims.tasks.taxa_validation import taxa_validation_task


class TaxaUploadView(DataUploadView):
    """Taxa upload view."""
    template_name = 'taxa_uploader.html'
    upload_task = taxa_upload
    category = 'taxa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add validation sessions to context
        context['validation_sessions'] = UploadSession.objects.filter(
            uploader=self.request.user,
            processed=False,
            canceled=False,
            process_file__isnull=False,
            category='taxa_validation'
        )
        context['finished_validation_sessions'] = UploadSession.objects.filter(
            Q(processed=True) | Q(canceled=True),
            uploader=self.request.user,
            category='taxa_validation'
        ).order_by('-uploaded_at')[:10]
        return context

    def post(self, request, *args, **kwargs):
        # Check if this is a validation request
        is_validation = request.POST.get('validate_only') == 'true'

        if is_validation:
            return self._handle_validation(request)
        else:
            return super().post(request, *args, **kwargs)

    def _handle_validation(self, request):
        """Handle validation-only request."""
        upload_file = request.FILES.get('csv_file')
        taxon_group_id = request.POST.get('taxon_group', None)

        cancel = ast.literal_eval(request.POST.get('cancel', 'False'))
        if cancel:
            session_id = request.POST.get('canceled_session_id', '')
            try:
                upload_session = UploadSession.objects.get(id=int(session_id))
                upload_session.canceled = True
                upload_session.save()
                return HttpResponseRedirect(request.path_info)
            except (UploadSession.DoesNotExist, ValueError):
                pass

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
                        category='taxa_validation'
                    )
                    upload_session.process_file.save(csv_file_name, csv_content)
            elif file_extension == '.csv':
                upload_session = UploadSession.objects.create(
                    uploader=request.user,
                    process_file=upload_file,
                    uploaded_at=datetime.now(),
                    module_group_id=taxon_group_id,
                    category='taxa_validation'
                )
            else:
                raise Http404('Unsupported file type')

        except Exception as e:
            raise Http404(f'Failed to process file: {str(e)}')

        taxa_validation_task.delay(upload_session.id)
        return HttpResponseRedirect(request.path_info)
