# -*- coding: utf-8 -*-
import os
import dateutil.parser
import pandas_access as mdb
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from geonode.people.models import Profile
from bims.models.fbis_uuid import FbisUUID
from bims.models.profile import Profile as BimsProfile


class Command(BaseCommand):
    help = 'Migrate data from fbis database'

    def handle(self, *args, **options):
        # check if file exists
        accdb_filename = 'rivers_dump_relevant_tables.accdb'
        accdb_filepath = os.path.join(
            settings.MEDIA_ROOT,
            accdb_filename
        )
        if not os.path.isfile(accdb_filepath):
            print('%s not found in media directory' % accdb_filename)
            return

        # Read a small table.
        df = mdb.read_table(accdb_filepath, "User")
        dhead = df.head(len(df))
        ctype = ContentType.objects.get_for_model(Profile)

        for i in range(len(dhead)):
            password_value = 'sha1${salt}${hash}'.format(
                salt=str(dhead['SaltValue'][i]),
                hash=str(dhead['PasswordHash'][i])
            )
            username_value = dhead['UserName'][i].replace(' ', '_').lower()
            date_joined = dateutil.parser.parse(dhead['DateFrom'][i])
            profile, created = Profile.objects.get_or_create(
                username=username_value,
                first_name=dhead['FirstName'][i],
                last_name=dhead['Surname'][i],
                email=dhead['Email'][i],
                date_joined=date_joined,
                fax=str(dhead['FaxNumber'][i]),
                delivery=dhead['PostalAddress'][i],
                zipcode=dhead['PostalCode'][i],
                position=dhead['Qualifications'][i],
                voice=str(dhead['Telephone'][i]),
                password=password_value,
                is_active=True,
            )

            # Other information
            bims_profile, bims_created = BimsProfile.objects.get_or_create(
                user=profile,
                qualifications=dhead['Qualifications'][i],
                fbis_username=dhead['UserName'][i],
                other=dhead['Other'][i],
                data={
                    'PasswordHint': str(dhead['PasswordHint'][i]),
                    'RegionPolID': str(dhead['RegionPolID'][i]),
                    'OrganisationID': str(dhead['OrganisationID'][i]),
                    'RegionalChampion': str(dhead['RegionalChampion'][i]),
                    'NTUserName': str(dhead['NTUserName'][i]),
                    'SASS4': str(dhead['SASS4'][i]),
                    'RipVegIndex': str(dhead['RipVegIndex'][i]),
                    'FAIIndex': str(dhead['FAIIndex'][i]),
                    'DateModified': str(dhead['DateModified'][i])
                }
            )

            fbis_uuid = FbisUUID.objects.create(
                content_type=ctype,
                object_id=profile.id,
                uuid=dhead['UserID'][i]
            )
