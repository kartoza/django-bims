from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response
from bims.location_site.river import fetch_river_name


class GetRiverName(LoginRequiredMixin, APIView):

    def get(self, request):
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)
        river_name = fetch_river_name(lat, lon)
        return Response({
            'river': river_name
        })
