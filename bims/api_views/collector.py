# coding=utf-8
import json
from django.http.response import HttpResponse
from django.db.models import CharField, Value as V
from django.db.models.functions import Concat
from rest_framework.views import APIView
from bims.models.biological_collection_record import BiologicalCollectionRecord
from sass.models import SiteVisit


class CollectorList(APIView):
    """API for listing all biological collection record collectors."""

    def get(self, request, *args):
        owners = (
            SiteVisit.objects.all().exclude(
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
        collectors = (
            BiologicalCollectionRecord.objects.filter(
                validated=True
            ).exclude(
                collector__exact='',
            ).annotate(
                full_name=Concat(
                    'collector_user__first_name', V(' '),
                    'collector_user__last_name',
                    output_field=CharField()
                )
            ).exclude(
                source_collection='gbif'
            ).distinct('full_name').order_by(
                'full_name'
            ).values_list('full_name', flat=True)
        )
        all_users = list(owners) + list(collectors)
        all_users = list(set(all_users))
        all_users.sort()
        user_index = 0
        if len(all_users) > 0:
            while all_users[user_index] == ' ':
                user_index += 1
        return HttpResponse(
            json.dumps(all_users[user_index:]),
            content_type='application/json'
        )
