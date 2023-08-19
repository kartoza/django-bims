import copy
import os
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.contrib.sites.models import Site
import csv

import pytz

from bims.location_site.river import fetch_river_name
from bims.models.location_site import generate_site_code, LocationSite
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.views.location_site import handle_location_site_post_data


class AddLocationSiteView(APIView):
    permission_classes = (IsAuthenticated,)

    def send_location_site_email(self, location_site: LocationSite):
        """
        Send the new location site data to the user and staff.
        Create CSV from location site and attach it to email.
        """
        current_site = Site.objects.get_current()

        csv_data = [
            ["ID", "Site Code", "User Site Code", "River Name",
             "User River Name", "Description", "Owner", "URL"],
            [location_site.id,
             location_site.site_code,
             location_site.legacy_site_code,
             location_site.river.name if location_site.river else '-',
             location_site.legacy_river_name,
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
            'from@example.com',
            [self.request.user.email],
            bcc=bcc_recipients
        )
        email.attach_file(csv_file_name)
        email.send()

        os.remove(csv_file_name)

    def post(self, request, *args, **kwargs):
        post_data = copy.deepcopy(request.data)

        # Fetch river name
        river_name = post_data.get('river_name', '')
        if not river_name:
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

        self.send_location_site_email(location_site)

        return Response(
            {
                'id': location_site.id,
                'site_code': site_code
            }
        )
