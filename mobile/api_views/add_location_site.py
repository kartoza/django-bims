import copy
import os
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.contrib.sites.models import Site
from django.conf import settings
import csv

import pytz

from bims.location_site.river import fetch_river_name
from bims.models.location_site import generate_site_code, LocationSite
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

    def send_location_site_email(self, location_site: LocationSite):
        """
        Send the new location site data to the user and staff.
        Create CSV from location site and attach it to email.
        """
        current_site = Site.objects.get_current()

        csv_data = [
            ["ID", "Site Code", "Ecosystem Type",
             "User Site Code",
             "River Name",
             "User River Name",
             "Wetland Name",
             "User Wetland Name",
             "Description", "Owner", "URL"],
            [location_site.id,
             location_site.site_code,
             location_site.ecosystem_type.capitalize(),
             location_site.legacy_site_code,
             location_site.river.name if location_site.river else '-',
             location_site.legacy_river_name,
             location_site.wetland_name,
             location_site.user_wetland_name,
             location_site.site_description,
             location_site.owner.username,
             'http://{url}/location-site-form/update/?id={id}'.format(
                 url=current_site,
                 id=location_site.id
             )
             ]]

        # Write CSV data to a file
        csv_file_name = f"location_site_{location_site.id}.csv"
        with open(csv_file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_data)

        email_body = """
        You have received the following notice from {current_site}:
        
        A new location site has been submitted through the mobile app. 
        Details of the submission are attached in the CSV file.
        """.format(current_site=current_site)

        bcc_recipients = list(
            get_user_model().objects.filter(is_superuser=True).values_list('email', flat=True)
        )

        owner_email = self.request.user.email

        if owner_email in bcc_recipients:
            bcc_recipients.remove(owner_email)

        # Send an email with the attached CSV
        email = EmailMessage(
            '[{}] New Location Site Data Submission'.format(current_site),
            email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.request.user.email],
            bcc=bcc_recipients
        )
        email.attach_file(csv_file_name)
        email.send()

        os.remove(csv_file_name)

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

        self.send_location_site_email(location_site)

        return Response(
            LocationSiteSerializer(location_site).data
        )
