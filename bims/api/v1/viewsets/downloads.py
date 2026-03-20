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

            def get_status(d):
                """Derive status from model fields."""
                if d.rejected:
                    return 'REJECTED'
                if d.approved and not d.processing:
                    return 'SUCCESS'
                if d.processing:
                    return 'PROCESSING'
                return 'PENDING'

            def get_download_url(d):
                """Get download URL if file exists."""
                try:
                    if d.request_file and d.request_file.name:
                        return d.request_file.url
                except (ValueError, AttributeError):
                    pass
                return None

            data = [
                {
                    "id": d.id,
                    "request_date": d.request_date.isoformat() if d.request_date else None,
                    "resource_type": d.resource_type,
                    "resource_name": d.resource_name or d.request_category or 'Download',
                    "status": get_status(d),
                    "download_url": get_download_url(d),
                    "progress": d.progress or '',
                    "approved": d.approved,
                    "rejected": d.rejected,
                    "processing": d.processing,
                }
                for d in downloads
            ]

            return success_response(
                data=data,
                meta={"count": len(data)},
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return success_response(
                data=[],
                meta={"count": 0, "error": str(e)},
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
        from bims.tasks.checklist import download_checklist
        from bims.models.download_request import DownloadRequest, DownloadRequestPurpose
        from bims.models.taxon_group import TaxonGroup

        taxon_group_id = request.data.get("taxon_group_id")
        boundary_id = request.data.get("boundary_id")

        if not taxon_group_id:
            return validation_error_response({"detail": "taxon_group_id is required"})

        try:
            # Get the taxon group
            try:
                taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
            except TaxonGroup.DoesNotExist:
                return validation_error_response({"detail": "Invalid taxon_group_id"})

            # Build dashboard URL with filters (this is how the checklist system works)
            filters = [f"modules={taxon_group_id}"]
            if boundary_id:
                filters.append(f"boundary={boundary_id}")
            dashboard_url = "&".join(filters)

            # Get or create a default purpose
            purpose, _ = DownloadRequestPurpose.objects.get_or_create(
                name="Species Checklist",
                defaults={"order": 1}
            )

            # Create download request
            download_request = DownloadRequest.objects.create(
                requester=request.user,
                resource_type=DownloadRequest.PDF,
                resource_name=f"{taxon_group.name} Checklist",
                purpose=purpose,
                dashboard_url=dashboard_url,
                approved=True,  # Auto-approve for authenticated users
                processing=True,
            )

            # Start the checklist generation task
            task = download_checklist.delay(
                download_request_id=download_request.id,
                send_email=False,
                user_id=request.user.id,
            )

            return success_response(
                data={
                    "task_id": task.id,
                    "download_request_id": download_request.id,
                    "status": "PENDING",
                    "message": "Checklist download request submitted",
                },
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
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
