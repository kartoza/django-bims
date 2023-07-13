import os
import json

from braces.views import SuperuserRequiredMixin
from django.http import Http404, HttpResponse, JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from rest_framework.views import APIView
from rest_framework.response import Response

from bims.models import (
    DecisionSupportTool
)
from bims.tasks.decision_support_tool import process_decision_support_tool


class DecisionSupportToolList(APIView):
    """API for listing all decision support tools."""

    def get(self, request, *args):
        dst = DecisionSupportTool.objects.all().values_list(
            'dst_name__name', flat=True
        ).order_by('dst_name__name').distinct('dst_name__name')
        return HttpResponse(
            json.dumps(list(dst)),
            content_type='application/json'
        )


class DecisionSupportToolView(SuperuserRequiredMixin, APIView):

    def post(self, request):
        dst_file = request.FILES.get('dst_file', None)

        if not dst_file:
            raise Http404('Missing csv file!')

        dst_file_path = os.path.join(
            settings.MEDIA_ROOT,
            'dst_folder'
        )
        if not os.path.exists(dst_file_path):
            os.mkdir(dst_file_path)

        fs = FileSystemStorage(location=dst_file_path)
        filename = fs.save(dst_file.name, dst_file)

        task = process_decision_support_tool.delay(
            os.path.join(
                dst_file_path, filename
            )
        )

        cache.set('DST_PROCESS', {
            'state': 'STARTED',
            'status': {},
            'task_id': task.task_id
        })

        return Response({
            'process_id': task.task_id
        })


def check_dst_status(request):
    if not request.user.is_superuser or not request.user.is_staff:
        raise Http404()
    dst_process = cache.get('DST_PROCESS')
    if dst_process:
        return JsonResponse(dst_process)
    else:
        return JsonResponse({})
