# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for download operations in API v1.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from bims.api.v1.responses import (
    error_response,
    success_response,
    validation_error_response,
)


class DownloadViewSet(viewsets.ViewSet):
    """
    ViewSet for async download operations.

    Endpoints:
    - GET /api/v1/downloads/ - List user's download requests
    - POST /api/v1/downloads/csv/ - Request CSV download
    - POST /api/v1/downloads/checklist/ - Request checklist download
    - GET /api/v1/downloads/{task_id}/status/ - Check download status
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        List user's download requests.

        Returns recent download tasks for the authenticated user.
        """
        from bims.models.download_request import DownloadRequest

        try:
            # Get download requests for current user
            downloads = DownloadRequest.objects.filter(
                requester=request.user
            ).order_by('-request_date')[:50]

            data = [
                {
                    "id": d.id,
                    "task_id": d.celery_task_id,
                    "request_date": d.request_date.isoformat() if d.request_date else None,
                    "request_type": d.request_type,
                    "status": d.processing_status,
                    "download_url": d.download_file.url if d.download_file else None,
                    "progress": d.progress or 0,
                }
                for d in downloads
            ]

            return success_response(
                data=data,
                meta={"count": len(data)},
            )
        except Exception as e:
            # If DownloadRequest model doesn't exist, return empty list
            return success_response(
                data=[],
                meta={"count": 0, "note": "Download tracking not yet configured"},
            )

    @action(detail=False, methods=["post"])
    def csv(self, request):
        """
        Request a CSV download of biological records.

        Body:
        - filters: Filter parameters for the records
        """
        from bims.download.csv_download import download_csv_task

        filters = request.data.get("filters", {})

        # Start async download task
        try:
            task = download_csv_task.delay(
                user_id=request.user.id,
                filters=filters,
            )

            return success_response(
                data={
                    "task_id": task.id,
                    "status": "PENDING",
                    "message": "Download request submitted",
                },
                meta={"filters": filters},
            )
        except Exception as e:
            return error_response(
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def checklist(self, request):
        """
        Request a checklist download.

        Body:
        - taxon_group_id: Taxon group to generate checklist for
        - boundary_id: Optional boundary filter
        """
        from bims.tasks.download_checklist import download_checklist_task

        taxon_group_id = request.data.get("taxon_group_id")
        boundary_id = request.data.get("boundary_id")

        if not taxon_group_id:
            return validation_error_response({"detail": "taxon_group_id is required"})

        try:
            task = download_checklist_task.delay(
                user_id=request.user.id,
                taxon_group_id=taxon_group_id,
                boundary_id=boundary_id,
            )

            return success_response(
                data={
                    "task_id": task.id,
                    "status": "PENDING",
                    "message": "Checklist download request submitted",
                },
            )
        except Exception as e:
            return error_response(
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="(?P<task_id>[\\w-]+)/status")
    def status(self, request, task_id=None):
        """
        Check the status of a download task.
        """
        from celery.result import AsyncResult

        if not task_id:
            return validation_error_response({"detail": "task_id is required"})

        try:
            result = AsyncResult(task_id)

            data = {
                "task_id": task_id,
                "status": result.status,
                "ready": result.ready(),
            }

            if result.ready():
                if result.successful():
                    data["result"] = result.result
                else:
                    data["error"] = str(result.result) if result.result else "Unknown error"

            return success_response(data=data)

        except Exception as e:
            return error_response(
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
