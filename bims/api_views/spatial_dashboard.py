# coding=utf-8
import hashlib
import json

from braces.views import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response

from bims.models.search_process import (
    SPATIAL_DASHBOARD_CONS_STATUS,
    SPATIAL_DASHBOARD_RLI,
    SPATIAL_DASHBOARD_MAP,
    SPATIAL_DASHBOARD_SUMMARY,
    SPATIAL_DASHBOARD_SPECIES_DOWNLOAD,
    SPATIAL_DASHBOARD_NATIONAL_CONS_STATUS,
    SEARCH_RESULTS,
    SEARCH_PROCESSING
)
from bims.models.search_process import SearchProcess
from bims.tasks.spatial_dashboard import (
    spatial_dashboard_cons_status,
    spatial_dashboard_rli,
    spatial_dashboard_map,
    spatial_dashboard_summary,
    spatial_dashboard_species_download,
    spatial_dashboard_national_cons_status,
)
from bims.utils.search_process import get_or_create_search_process


def _opensearch_available():
    try:
        from django.conf import settings
        if not getattr(settings, 'OPENSEARCH_HOST', None):
            return False
        from bims.opensearch.client import get_client
        get_client().info()
        return True
    except Exception:
        return False


class SpatialDashboardBaseApiView(LoginRequiredMixin, APIView):
    search_type = None
    task = None
    os_task = None

    def _pick_task(self):
        if self.os_task is not None and _opensearch_available():
            return self.os_task
        return self.task

    def get(self, request):
        search_uri = request.build_absolute_uri()
        search_process, _ = get_or_create_search_process(
            search_type=self.search_type,
            query=search_uri,
            requester=request.user
        )

        results = search_process.get_file_if_exits()
        if results:
            return Response(results)

        data_for_process_id = {
            'search_uri': search_uri
        }
        process_id = hashlib.sha256(
            json.dumps(data_for_process_id, sort_keys=True).encode('utf-8')
        ).hexdigest()

        search_process.set_process_id(process_id)
        search_process.set_status(SEARCH_PROCESSING)
        task = self._pick_task().delay(
            search_parameters=request.GET.dict(),
            search_process_id=search_process.id
        )

        result_file = search_process.get_file_if_exits(finished=False)
        if result_file:
            result_file['task_id'] = task.id
            return Response(result_file)

        return Response({
            'status': SEARCH_PROCESSING,
            'process': process_id,
            'task_id': task.id
        })


class SpatialDashboardConsStatusApiView(SpatialDashboardBaseApiView):
    from bims.tasks.opensearch_spatial_dashboard import (
        opensearch_spatial_dashboard_cons_status,
    )
    search_type = SPATIAL_DASHBOARD_CONS_STATUS
    task = spatial_dashboard_cons_status
    os_task = opensearch_spatial_dashboard_cons_status


class SpatialDashboardRliApiView(SpatialDashboardBaseApiView):
    from bims.tasks.opensearch_spatial_dashboard import (
        opensearch_spatial_dashboard_rli,
    )
    search_type = SPATIAL_DASHBOARD_RLI
    task = spatial_dashboard_rli
    os_task = opensearch_spatial_dashboard_rli


class SpatialDashboardMapApiView(SpatialDashboardBaseApiView):
    from bims.tasks.opensearch_spatial_dashboard import (
        opensearch_spatial_dashboard_map,
    )
    search_type = SPATIAL_DASHBOARD_MAP
    task = spatial_dashboard_map
    os_task = opensearch_spatial_dashboard_map

    def get(self, request):
        search_url = request.build_absolute_uri().replace(
            '/api/spatial-dashboard/map/',
            '/api/collection-search/'
        )
        existing = (
            SearchProcess.objects.filter(
                category=SEARCH_RESULTS,
                query=search_url,
                requester=request.user,
                finished=True
            )
            .exclude(search_raw_query__isnull=True)
            .exclude(process_id__isnull=True)
            .first()
        )
        if existing:
            existing_data = existing.get_file_if_exits()
            if existing_data:
                return Response({
                    'extent': existing_data.get('extent', []),
                    'sites_raw_query': existing.process_id
                })
        return super(SpatialDashboardMapApiView, self).get(request)


class SpatialDashboardSummaryApiView(SpatialDashboardBaseApiView):
    from bims.tasks.opensearch_spatial_dashboard import (
        opensearch_spatial_dashboard_summary,
    )
    search_type = SPATIAL_DASHBOARD_SUMMARY
    task = spatial_dashboard_summary
    os_task = opensearch_spatial_dashboard_summary


class SpatialDashboardSpeciesDownloadApiView(SpatialDashboardBaseApiView):
    from bims.tasks.opensearch_spatial_dashboard import (
        opensearch_spatial_dashboard_species_download,
    )
    search_type = SPATIAL_DASHBOARD_SPECIES_DOWNLOAD
    task = spatial_dashboard_species_download
    os_task = opensearch_spatial_dashboard_species_download


class SpatialDashboardNationalConsStatusApiView(SpatialDashboardBaseApiView):
    from bims.tasks.opensearch_spatial_dashboard import (
        opensearch_spatial_dashboard_national_cons_status,
    )
    search_type = SPATIAL_DASHBOARD_NATIONAL_CONS_STATUS
    task = spatial_dashboard_national_cons_status
    os_task = opensearch_spatial_dashboard_national_cons_status
