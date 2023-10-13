import copy
from datetime import datetime

import pytz

from bims.location_site.river import fetch_river_name
from bims.models.location_site import generate_site_code
from bims.tasks.email_csv import send_location_site_email
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.views.location_site import handle_location_site_post_data
from bims.enums.ecosystem_type import (
    ECOSYSTEM_RIVER, ECOSYSTEM_WETLAND
)
from bims.serializers.location_site_serializer import (
    LocationSiteSerializer
)


class AddLocationSiteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        post_data = copy.deepcopy(request.data)

        ecosystem_type = post_data.get(
            'ecosystem_type', ECOSYSTEM_RIVER).capitalize()
        river_name = post_data.get('river_name', '')
        site_code = '-'
        user_wetland_name = post_data.get('user_wetland_name', '')
        wetland_data = None

        if ecosystem_type == ECOSYSTEM_WETLAND:
            wetland_data = post_data.get('wetland_data', None)
            if wetland_data:
                if 'hgm_type' in wetland_data:
                    post_data['hydrogeomorphic_type'] = wetland_data['hgm_type']
                if 'wetlid' in wetland_data:
                    post_data['wetland_id'] = wetland_data['wetlid']
        else:
            # Fetch river name
            if not river_name:
                river_name = fetch_river_name(
                    post_data.get('latitude'),
                    post_data.get('longitude'))

        post_data['legacy_site_code'] = post_data.get('site_code')
        post_data['site_code'] = site_code
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

        if wetland_data:
            location_site.additional_data = wetland_data
            location_site.save()

        # Generate site code
        site_code, catchments_data = generate_site_code(
            location_site=location_site,
            lat=location_site.latitude,
            lon=location_site.longitude,
            river_name=river_name,
            ecosystem_type=ecosystem_type,
            wetland_name=user_wetland_name
        )

        location_site.site_code = site_code
        location_site.name = site_code
        location_site.save()

        send_location_site_email.delay(
            location_site.id, self.request.user.id)

        return Response(
            LocationSiteSerializer(location_site).data
        )
