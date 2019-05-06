# -*- coding: utf-8 -*-
import dateutil.parser
from geonode.people.models import Profile
from bims.models.profile import Profile as BimsProfile
from sass.scripts.fbis_importer import FbisImporter


class FbisUserImporter(FbisImporter):

    content_type_model = Profile
    table_name = 'User'

    def process_row(self, row, index):
        # print(row)
        password_value = 'sha1${salt}${hash}'.format(
            salt=str(self.get_row_value('SaltValue', row)),
            hash=str(self.get_row_value('PasswordHash', row))
        )
        username_value = self.get_row_value('UserName', row).replace(
            ' ', '_').lower()
        date_joined = dateutil.parser.parse(
            self.get_row_value('DateFrom', row))
        email_value = self.get_row_value('Email', row)
        if Profile.objects.filter(username=username_value).exists():
            profiles = Profile.objects.filter(username=username_value)
            if not profiles.filter(email=email_value).exists():
                same_username = len(profiles)
                username_value += '_%s' % str(same_username)
        profile, created = Profile.objects.get_or_create(
            username=username_value,
            email=self.get_row_value('Email', row),
            is_active=True,
        )

        profile.first_name = self.get_row_value('FirstName', row)
        profile.last_name = self.get_row_value('Surname', row)
        profile.date_joined = date_joined
        profile.fax = str(self.get_row_value('FaxNumber', row))
        profile.delivery = self.get_row_value('PostalAddress', row)
        profile.zipcode = self.get_row_value('PostalCode', row)
        profile.position = self.get_row_value('Qualifications', row)
        profile.voice = str(self.get_row_value('Telephone', row))
        profile.password = password_value
        profile.save()

        # Other information
        bims_profile, bims_created = BimsProfile.objects.get_or_create(
            user=profile,
        )

        bims_profile.qualifications = self.get_row_value('Qualifications', row)
        bims_profile.full_name = self.get_row_value('UserName', row)
        bims_profile.other = self.get_row_value('Other', row)
        bims_profile.data = {
            'PasswordHint': str(self.get_row_value('PasswordHint', row)),
            'RegionPolID': str(self.get_row_value('RegionPolID', row)),
            'OrganisationID': str(self.get_row_value('OrganisationID', row)),
            'RegionalChampion': str(self.get_row_value(
                'RegionalChampion',
                row)),
            'NTUserName': str(self.get_row_value('NTUserName', row)),
            'SASS4': str(self.get_row_value('SASS4', row)),
            'RipVegIndex': str(self.get_row_value('RipVegIndex', row)),
            'FAIIndex': str(self.get_row_value('FAIIndex', row)),
            'DateModified': str(self.get_row_value('DateModified', row))
        }
        bims_profile.save()

        self.save_uuid(
            uuid=self.get_row_value('UserID', row),
            object_id=profile.id
        )
