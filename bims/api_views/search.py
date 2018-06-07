# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '07/06/18'

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.documents import BiologicalCollectionRecordDocument


class SearchObjects(APIView):
    """API for searching using elasticsearch."""

    def get(self, request, original_species_name):
        s = BiologicalCollectionRecordDocument.search().query(
            "match", original_species_name=original_species_name)

        data = {}
        if s.count() > 0:
            for hit in s:
                data['original_species_name'] = hit.original_species_name
                data['collection_date'] = hit.collection_date
                data['collector'] = hit.collector
        else:
            data['results'] = 'Not Found'

        return Response(data)