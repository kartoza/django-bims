from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.location_site.river import fetch_river_name
from sass.models import River


class FetchRiverName(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args):
        lat = request.GET.get('lat', '')
        lon = request.GET.get('lon', '')

        river_name = fetch_river_name(
            lat,
            lon
        )

        try:
            River.objects.get_or_create(
                name=river_name
            )
        except River.MultipleObjectsReturned:
            pass

        return Response({
            'river_name': river_name
        })
