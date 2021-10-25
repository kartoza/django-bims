# coding=utf-8
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.source_reference import SourceReference


class UnpublishedData(APIView):
    """API create unpublished data."""

    def post(self, request, *args):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        data = request.data
        try:
            unpublished = SourceReference.objects.create(
                note=data['note'],
                source_name=data.get('source', None),
            )
        except Exception as e:
            return HttpResponseBadRequest('%s' % e)
        return Response(
            {'note': unpublished.note, 'id': unpublished.id}
            )
