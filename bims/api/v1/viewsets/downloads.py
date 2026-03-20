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
    - POST /api/v1/downloads/taxa-list/ - Request taxa list download
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
                import os
                from django.conf import settings
                try:
                    if d.request_file and d.request_file.name:
                        file_name = d.request_file.name
                        # Handle old records with absolute paths stored in the field
                        if os.path.isabs(file_name):
                            # Try to extract relative path from MEDIA_ROOT
                            if settings.MEDIA_ROOT in file_name:
                                relative_path = os.path.relpath(file_name, settings.MEDIA_ROOT)
                                return f"{settings.MEDIA_URL}{relative_path}"
                            # Fallback: just use the filename
                            return f"{settings.MEDIA_URL}{os.path.basename(file_name)}"
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

            # Build dashboard URL with filters in fragment format
            # The parse_url_to_filters function expects URL with fragment containing query params
            filter_parts = [f"modules={taxon_group_id}"]
            if boundary_id:
                filter_parts.append(f"boundary={boundary_id}")
            # Format: /map/#site-detail/?modules=X&boundary=Y
            dashboard_url = f"/map/#site-detail/?{'&'.join(filter_parts)}"

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

    @action(detail=False, methods=["post"], url_path="taxa-list")
    def taxa_list(self, request):
        """
        Request a taxa list download.

        Body:
        - taxon_group_id: Taxon group to download taxa for
        - output: Output format ('csv' or 'xlsx'), defaults to 'csv'
        - filters: Optional additional filters
        """
        import datetime
        import hashlib
        import os
        from django.conf import settings
        from bims.tasks.download_taxa_list import download_taxa_list_task
        from bims.tasks.email_csv import send_csv_via_email
        from bims.models.taxon_group import TaxonGroup
        from bims.models.download_request import DownloadRequest, DownloadRequestPurpose

        taxon_group_id = request.data.get("taxon_group_id")
        output = request.data.get("output", "csv")
        filters = request.data.get("filters", {})

        if not taxon_group_id:
            return validation_error_response({"detail": "taxon_group_id is required"})

        try:
            try:
                taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
            except TaxonGroup.DoesNotExist:
                return validation_error_response({"detail": "Invalid taxon_group_id"})

            # Build filter dict for the task (mimicking legacy GET params)
            filter_dict = {"taxonGroup": str(taxon_group_id), "output": output}
            filter_dict.update(filters)

            current_time = datetime.datetime.now()
            filter_hash = hashlib.md5(str(filter_dict).encode()).hexdigest()[:8]

            filename = (
                f'{taxon_group.name}-{current_time.year}-'
                f'{current_time.month}-{current_time.day}-'
                f'{current_time.hour}-{filter_hash}'
            ).replace(' ', '_')

            folder = settings.PROCESSED_CSV_PATH
            path_folder = os.path.join(settings.MEDIA_ROOT, folder)
            path_file = os.path.join(path_folder, filename)

            if not os.path.exists(path_folder):
                os.makedirs(path_folder, exist_ok=True)

            # Get or create a default purpose
            purpose, _ = DownloadRequestPurpose.objects.get_or_create(
                name="Taxa List",
                defaults={"order": 2}
            )

            # Create download request for tracking
            download_request = DownloadRequest.objects.create(
                requester=request.user,
                resource_type=DownloadRequest.XLS if output == 'xlsx' else DownloadRequest.CSV,
                resource_name=f"{taxon_group.name} Taxa List",
                purpose=purpose,
                dashboard_url=f"taxonGroup={taxon_group_id}",
                approved=True,
                processing=True,
            )

            if os.path.exists(path_file):
                # File already exists, send it via email
                send_csv_via_email.delay(
                    user_id=request.user.id,
                    csv_file=path_file,
                    file_name=filename,
                    approved=True,
                    download_request_id=download_request.id,
                )
            else:
                # Start the async task
                download_taxa_list_task.delay(
                    filter_dict,
                    csv_file=path_file,
                    filename=filename,
                    user_id=request.user.id,
                    output=output,
                    download_request_id=download_request.id,
                    taxon_group_id=taxon_group_id
                )

            return success_response(
                data={
                    "download_request_id": download_request.id,
                    "status": "PROCESSING",
                    "message": "Taxa list download request submitted. You will receive an email when ready.",
                    "filename": filename,
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
