# -*- coding: utf-8 -*-
import logging
import os
import csv
from geonode.people.models import Profile
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.sites.models import Site
from bims.models.profile import Profile as BimsProfile

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        users = Profile.objects.all()
        domain = Site.objects.get_current().domain
        csv_path = os.path.join(settings.MEDIA_ROOT, 'users_csv')
        if not os.path.exists(csv_path) : os.mkdir(csv_path)
        csv_file_path = os.path.join(csv_path, 'all_users.csv')

        with open(csv_file_path, mode='w') as csv_file:
            writer = csv.writer(
                csv_file, delimiter=',', quotechar='"',
                quoting=csv.QUOTE_MINIMAL)
            writer.writerow([
                'Username', 'Email address', 'First name', 'Last name',
                'Active', 'Staff',
                'Last login',
                'Date joined',
                'Link',
                'SASS Accredited date from',
                'SASS Accredited date to',
                'Is Accredited',
                'Role'
            ])
            for user in users:
                csv_data = []
                csv_data.append(user.username)
                csv_data.append(user.email)
                csv_data.append(user.first_name)
                csv_data.append(user.last_name)
                csv_data.append(user.is_active)
                csv_data.append(user.is_staff)
                csv_data.append(user.last_login)
                csv_data.append(user.date_joined)
                link = 'http://{d}/admin/people/profile/{id}/'.format(
                    d=domain,
                    id=user.id
                )
                csv_data.append(link)
                try:
                    bims_profile = BimsProfile.objects.get(
                        user=user
                    )
                    csv_data.append(
                        bims_profile.sass_accredited_date_from
                    )
                    csv_data.append(
                        bims_profile.sass_accredited_date_to
                    )
                    csv_data.append(
                        bims_profile.is_accredited()
                    )
                    csv_data.append(
                        bims_profile.role
                    )
                except BimsProfile.DoesNotExist:
                    pass
                writer.writerow(csv_data)
