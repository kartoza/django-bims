# coding=utf-8
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.source_reference import DatabaseRecord
from bims.serializers.database_record import DatabaseRecordSerializer


class DatabaseRecordsList(APIView):
    """API for listing all database record of source reference."""

    def get(self, request, *args):
        return Response(
            DatabaseRecordSerializer(
                DatabaseRecord.objects.all(), many=True).data)

    def post(self, request, *args):
        if not request.user.is_authenticated():
            return HttpResponseForbidden()
        data = request.data
        try:
            record = DatabaseRecord.objects.create(
                name=data['name'],
                description=data.get('description', None),
                url=data.get('url', None),
            )
        except Exception as e:
            return HttpResponseBadRequest('%s' % e)
        return Response(
            DatabaseRecordSerializer(record).data)
