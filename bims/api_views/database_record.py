# coding=utf-8
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.source_reference import DatabaseRecord, SourceReferenceDatabase
from bims.serializers.database_record import DatabaseRecordSerializer


class DatabaseRecordsList(APIView):
    """API for listing all database record of source reference."""

    def get(self, request, *args):
        return Response(
            DatabaseRecordSerializer(
                DatabaseRecord.objects.all(), many=True).data)

    def post(self, request, *args):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        data = request.data
        try:
            record, created = DatabaseRecord.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data.get('description', None),
                    'url': data.get('url', None),
                }
            )
        except Exception as e:
            return HttpResponseBadRequest('%s' % e)

        source_date = (data.get('source_date', '') or '').strip() or None
        note = (data.get('note', '') or '').strip() or None

        if source_date or note:
            sr, _ = SourceReferenceDatabase.objects.get_or_create(source=record)
            if source_date is not None:
                sr.source_date = source_date or None
            if note is not None:
                sr.note = note
            sr.save()

        return Response(
            DatabaseRecordSerializer(record).data)
