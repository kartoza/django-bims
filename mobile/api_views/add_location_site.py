import copy
from datetime import datetime

import pytz

from bims.location_site.river import fetch_river_name
from bims.models.location_site import generate_site_code
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.views.location_site import handle_location_site_post_data


class AddLocationSiteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        post_data = copy.deepcopy(request.data)

        # Fetch river name
        river_name = fetch_river_name(
            post_data.get('latitude'), post_data.get('longitude'))

        # Generate site code
        site_code, catchments_data = generate_site_code(
            location_site=None,
            lat=post_data.get('latitude'),
            lon=post_data.get('longitude'),
            river_name=river_name
        )
        post_data['legacy_site_code'] = post_data.get('site_code')
        post_data['site_code'] = site_code
        post_data['catchment_geocontext'] = catchments_data
        post_data['river_name'] = river_name
        post_data['site_description'] = post_data.get('description')
        if 'date' in post_data:
            post_data['date'] = datetime.fromtimestamp(
                int(post_data.get('date')),
                pytz.UTC
            )

        location_site = handle_location_site_post_data(
            post_data,
            self.request.user
        )
        return Response(
            {
                'id': location_site.id,
                'site_code': site_code
            }
        )
