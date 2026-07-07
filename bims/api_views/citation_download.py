# coding=utf-8
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models.download_request import DownloadRequest

CITATION_FORMATS = ('bibtex', 'ris', 'plain')


class DownloadCitationsApi(APIView):
    """
    POST /api/download-citations/
    """

    def post(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        download_request_id = request.POST.get('download_request_id')
        if not download_request_id:
            return Response(
                {'error': 'download_request_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        download_request = get_object_or_404(
            DownloadRequest,
            id=download_request_id,
            requester=request.user,
        )

        raw_ids = request.POST.getlist('source_reference_ids')
        if not raw_ids:
            raw_ids = request.POST.get('source_reference_ids', '').split(',')
        source_reference_ids = [
            int(i) for i in raw_ids if str(i).strip().isdigit()
        ]

        raw_dataset_ids = request.POST.getlist('dataset_ids')
        if not raw_dataset_ids:
            raw_dataset_ids = request.POST.get('dataset_ids', '').split(',')
        dataset_ids = [
            int(i) for i in raw_dataset_ids if str(i).strip().isdigit()
        ]

        if not source_reference_ids and not dataset_ids:
            return Response(
                {'error': 'No source_reference_ids or dataset_ids provided'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        citation_format = request.POST.get('citation_format', 'plain').lower()
        if citation_format not in CITATION_FORMATS:
            return Response(
                {'error': f'citation_format must be one of {CITATION_FORMATS}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        download_request.download_params = {
            'citation_format': citation_format,
            'source_reference_ids': source_reference_ids,
            'dataset_ids': dataset_ids,
        }
        download_request.processing = True
        download_request.save(update_fields=['download_params', 'processing'])

        from bims.tasks.citation_download import generate_citation_download
        generate_citation_download.delay(
            download_request_id=download_request.id,
            source_reference_ids=source_reference_ids,
            citation_format=citation_format,
            user_id=request.user.id,
            dataset_ids=dataset_ids,
        )

        return Response(
            {'download_request_id': download_request.id},
            status=status.HTTP_202_ACCEPTED,
        )
