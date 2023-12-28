from django.http import (
    Http404, HttpResponseServerError, HttpResponseForbidden
)
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.source_reference import (
    SourceReference
)
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.models.chemical_record import (
    ChemicalRecord
)
from bims.models.decision_support_tool import DecisionSupportTool


class DeleteRecordsByReferenceId(APIView):
    """
    API endpoint for deleting BiologicalCollectionRecord and ChemicalRecord
    instances associated with a given SourceReference ID.
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden(
                'Only superusers are allowed to perform this action.'
            )

        source_reference_id = kwargs.get('source_reference_id')
        if not source_reference_id:
            raise Http404('Missing id')

        try:
            source_reference = get_object_or_404(
                SourceReference,
                pk=source_reference_id
            )
            messages = []
            bio_records = BiologicalCollectionRecord.objects.filter(source_reference_id=source_reference_id)
            if bio_records.exists():
                DecisionSupportTool.objects.filter(
                    biological_collection_record__id__in=list(bio_records.values_list('id', flat=True))
                ).delete()
                BiologicalCollectionRecord.objects.filter(source_reference_id=source_reference_id).delete()
                messages.append(
                    'BiologicalCollectionRecord successfully deleted'
                )
            else:
                messages.append("No BiologicalCollectionRecord found for the given reference ID.")

            if ChemicalRecord.objects.filter(source_reference_id=source_reference_id).exists():
                ChemicalRecord.objects.filter(source_reference_id=source_reference_id).delete()
                messages.append(
                    'ChemicalRecord successfully deleted'
                )
            else:
                messages.append("No ChemicalRecord found for the given reference ID.")

            return Response(
                        {'message': messages},
                        status=status.HTTP_200_OK)

        except Exception as e:
            # In case of any other error, return a 500 Internal Server Error
            return HttpResponseServerError(f'An error occurred: {e}')
