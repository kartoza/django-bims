# coding=utf-8
import json
from django.http.response import HttpResponse
from django.db.models import CharField, Value as V
from django.db.models.functions import Concat
from rest_framework.views import APIView
from bims.models.survey import Survey


class CollectorList(APIView):
    """API for listing all biological collection record collectors."""

    def get(self, request, *args):
        survey_owners = (
            Survey.objects.filter(
                biological_collection_record__isnull=False
            ).exclude(
                owner__isnull=True
            ).annotate(
                full_name=Concat(
                    'owner__first_name', V(' '), 'owner__last_name',
                    output_field=CharField()
                )
            ).distinct('full_name').order_by(
                'full_name'
            ).values_list('full_name', flat=True)
        )
        all_users = list(survey_owners)
        all_users.sort()
        user_index = 0
        if len(all_users) > 0:
            while all_users[user_index] == ' ':
                user_index += 1
        return HttpResponse(
            json.dumps(all_users[user_index:]),
            content_type='application/json'
        )
