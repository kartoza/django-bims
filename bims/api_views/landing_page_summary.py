from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models import (
    BiologicalCollectionRecord,
    LocationSite,
)
from sass.models.site_visit import SiteVisit



class LandingPageSummary(APIView):
    def get(self, request, *args):
        summary_data = list()

        # Location site
        summary_data.append({
            'key': 'sites',
            'title': 'Location Sites',
            'img': '',
            'icon': 'fa-map-marker',
            'value': LocationSite.objects.all().count()
        })

        # Collection records
        summary_data.append({
            'key': 'records',
            'title': 'Collection Records',
            'img': '',
            'icon': 'fa-table',
            'value': BiologicalCollectionRecord.objects.all().count()
        })

        # Site visits
        summary_data.append({
            'key': 'site_visits',
            'title': 'Site Visits',
            'img': '',
            'icon': 'fa-street-view',
            'value': SiteVisit.objects.all().count()
        })

        return Response(summary_data)
