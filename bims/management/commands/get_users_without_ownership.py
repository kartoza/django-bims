# coding=utf-8
import csv
import os
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from bims.models import (
    LocationSite,
    BiologicalCollectionRecord
)
from sass.models import (
    SiteVisit
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        all_users = get_user_model().objects.all()
        collection_owners = (
            BiologicalCollectionRecord.objects.all()
            .values_list('owner__id', flat=True)
            .distinct('owner')
        )
        all_users = all_users.exclude(
            id__in=list(filter(None, collection_owners)))
        print('Users unassociated to biological collection : {}'.format(
            all_users.count()
        ))

        site_owners = (
            LocationSite.objects.all()
            .values_list('creator__id', flat=True)
            .distinct('creator')
        )
        all_users = all_users.exclude(
            id__in=list(filter(None, site_owners))
        )
        print('Users unassociated to location site : {}'.format(
            all_users.count()
        ))

        site_visit_owners = (
            SiteVisit.objects.all()
            .values_list('owner__id', flat=True)
            .distinct('owner')
        )
        site_visit_assessors = (
            SiteVisit.objects.all()
            .values_list('assessor_id', flat=True)
            .distinct('assessor')
        )
        all_users = all_users.exclude(
            id__in=list(filter(None, site_visit_owners))
        )
        all_users = all_users.exclude(
            id__in=list(filter(None, site_visit_assessors))
        )
        print('Users unassociated to site visit : {}'.format(
            all_users.count()
        ))

        all_users = all_users.filter(
            bims_profile__data__SASS4__isnull=False
        )
        print('Users taken from fbis database : {}'.format(
            all_users.count()
        ))

        filename = 'users_without_ownership.csv'
        file_path = os.path.join(
            os.path.abspath(os.path.dirname(__name__)),
            '/home/web/media/{filename}'.format(
                filename=filename
            ))

        csv_header = [
            'Full Name',
            'First Name',
            'Last Name',
            'Email',
            'Date Joined',
            'Admin Page']
        with open(file_path, 'w') as csv_file:
            writer = csv.writer(csv_file, delimiter=',',
                                quoting=csv.QUOTE_MINIMAL)
            writer.writerow(csv_header)
            for user in all_users:
                writer.writerow([
                    user.get_full_name().encode('utf-8'),
                    user.first_name.encode('utf-8'),
                    user.last_name.encode('utf-8'),
                    user.email,
                    user.date_joined,
                    '{url}/admin/people/profile/{id}/change/'.format(
                        url=Site.objects.get_current(),
                        id=user.id
                    )
                ])
