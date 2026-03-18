# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for Celery task status in API v1.
"""
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bims.api.v1.responses import (
    error_response,
    success_response,
    validation_error_response,
)


class TaskStatusViewSet(viewsets.ViewSet):
    """
    ViewSet for checking Celery task status.

    Endpoints:
    - GET /api/v1/tasks/{task_id}/ - Get task status
    - DELETE /api/v1/tasks/{task_id}/ - Cancel/revoke task
    """

    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        """
        Get the status of a Celery task.
        """
        from celery.result import AsyncResult

        task_id = pk

        if not task_id:
            return validation_error_response({"detail": "task_id is required"})

        try:
            result = AsyncResult(task_id)

            data = {
                "task_id": task_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
            }

            # Add result or error info
            if result.ready():
                if result.successful():
                    # Be careful not to expose sensitive data
                    result_data = result.result
                    if isinstance(result_data, dict):
                        # Only include safe fields
                        safe_fields = ["url", "filename", "count", "message", "download_url"]
                        data["result"] = {k: v for k, v in result_data.items() if k in safe_fields}
                    else:
                        data["result"] = str(result_data) if result_data else None
                else:
                    data["error"] = str(result.result) if result.result else "Task failed"

            # Add progress info if available
            if hasattr(result, "info") and result.info:
                if isinstance(result.info, dict):
                    data["progress"] = result.info.get("progress")
                    data["current"] = result.info.get("current")
                    data["total"] = result.info.get("total")

            return success_response(data=data)

        except Exception as e:
            return error_response(
                errors={"detail": f"Error checking task status: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, pk=None):
        """
        Revoke/cancel a Celery task.
        """
        from celery.result import AsyncResult
        from django.conf import settings

        task_id = pk

        if not task_id:
            return validation_error_response({"detail": "task_id is required"})

        try:
            result = AsyncResult(task_id)

            if result.ready():
                return error_response(
                    errors={"detail": "Task has already completed"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Revoke the task
            result.revoke(terminate=True)

            return success_response(
                data={
                    "task_id": task_id,
                    "status": "REVOKED",
                    "message": "Task has been cancelled",
                }
            )

        except Exception as e:
            return error_response(
                errors={"detail": f"Error cancelling task: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
