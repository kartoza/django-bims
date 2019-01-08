# -*- coding: utf-8 -*-
import os
import dateutil.parser
import pandas_access as mdb
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from geonode.people.models import Profile
from bims.models.fbis_uuid import FbisUUID
from bims.models.profile import Profile as BimsProfile


def import_user_table(accdb_file_name):
    accdb_filepath = os.path.join(
        settings.MEDIA_ROOT,
        accdb_file_name
    )
    if not os.path.isfile(accdb_filepath):
        print('%s not found in media directory' % accdb_file_name)
        return

    # Read User table.
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
        email_value = dhead['Email'][i]
        if Profile.objects.filter(username=username_value).exists():
            profiles = Profile.objects.filter(username=username_value)
            if not profiles.filter(email=email_value).exists():
                same_username = len(profiles)
                username_value += '_%s' % str(same_username)
        profile, created = Profile.objects.get_or_create(
            username=username_value,
            email=dhead['Email'][i],
            is_active=True,
        )

        profile.first_name = dhead['FirstName'][i]
        profile.last_name = dhead['Surname'][i]
        profile.date_joined = date_joined
        profile.fax = str(dhead['FaxNumber'][i])
        profile.delivery = dhead['PostalAddress'][i]
        profile.zipcode = dhead['PostalCode'][i]
        profile.position = dhead['Qualifications'][i]
        profile.voice = str(dhead['Telephone'][i])
        profile.password = password_value
        profile.save()

        # Other information
        bims_profile, bims_created = BimsProfile.objects.get_or_create(
            user=profile,
        )

        bims_profile.qualifications = dhead['Qualifications'][i]
        bims_profile.fbis_username = dhead['UserName'][i]
        bims_profile.other = dhead['Other'][i]
        bims_profile.data = {
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
        bims_profile.save()

        fbis_uuid, fbis_created = FbisUUID.objects.get_or_create(
            content_type=ctype,
            object_id=profile.id,
            uuid=dhead['UserID'][i]
        )
