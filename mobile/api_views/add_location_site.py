from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.views.location_site import handle_location_site_post_data


class AddLocationSiteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        location_site = handle_location_site_post_data(
            request.POST.dict(),
            self.request.user
        )
        return Response(
            location_site.id
        )
