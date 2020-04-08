import os
import sqlite3
from uuid import UUID
from sqlite3 import Error
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from bims.models.fbis_uuid import FbisUUID
from geonode.people.models import Profile
from bims.models.profile import Profile as BimsProfile


class FbisImporter(object):

    is_sqlite = True
    postgres_database = ''
    postgres_user = ''
    postgres_password = ''
    postgres_host = ''
    postgres_port = 5432
    update_only = False
    only_missing = False
    new_data = []
    failed_messages = []

    def __init__(self, sqlite_filename, max_row = None):
        self.sqlite_filename = sqlite_filename
        self.table_colums = []
        self.sqlite_filepath = None
        self.sqlite_rows = None
        self.max_row = max_row
        self.content_type = None
        self.current_row = None

    def get_file_path(self):
        self.sqlite_filepath = os.path.join(
            settings.MEDIA_ROOT,
            self.sqlite_filename
        )
        if not os.path.isfile(self.sqlite_filepath):
            print('%s not found in media directory' % self.sqlite_filename)
            return False
        return True

    def get_object_from_uuid(self, column, model, uuid=None):
        content_object = None
        if not self.current_row:
            return None
        ctype = ContentType.objects.get_for_model(model)
        if not uuid:
            uuid = self.get_row_value(column, self.current_row)
            if uuid:
                uuid = uuid.upper()
        objects = FbisUUID.objects.filter(
            uuid__icontains=uuid,
            content_type=ctype
        )
        if objects.exists():
            for uuid_object in objects:
                if uuid_object.content_object:
                    content_object = uuid_object.content_object
        return content_object

    def create_connection(self):
        try:
            conn = sqlite3.connect(self.sqlite_filepath)
            return conn
        except Error as e:
            print(e)
        return None

    def select_table(self, conn):
        cur = conn.cursor()
        sql = "SELECT * FROM {table_name}".format(
            table_name=self.table_name
        )
        if self.max_row:
            sql += ' LIMIT {max}'.format(max=self.max_row)
        cur.execute(sql)
        self.sqlite_rows = cur.fetchall()
        cur.close()

    def get_table_colums(self, conn):
        cur = conn.cursor()
        sql = "SELECT * FROM {table_name} WHERE 1=0".format(
            table_name=self.table_name
        )
        if self.max_row:
            sql += ' LIMIT {max}'.format(max=self.max_row)
        cur.execute(sql)
        self.table_colums = [d[0] for d in cur.description]
        cur.close()

    def save_uuid(self, uuid, object_id):
        if not self.content_type:
            print('Empty content type')
            return
        FbisUUID.objects.get_or_create(
            content_type=self.content_type,
            object_id=object_id,
            uuid=uuid
        )

    def process_row(self, row, index):
        raise NotImplementedError

    def start_processing_rows(self):
        return

    def finish_processing_rows(self):
        return

    def get_row_value(self, column_name, row=None, return_none_if_empty=False):
        if not row:
            row = self.current_row
        try:
            column_index = self.table_colums.index(column_name)
        except ValueError:
            return None
        if column_index < 0:
            return None
        if not row[column_index]:
            if return_none_if_empty:
                return None
            return ''
        else:
            value = row[column_index]
            if isinstance(value, UUID):
                value = str(value)
            return value

    @property
    def content_type_model(self):
        raise NotImplementedError

    @property
    def table_name(self):
        raise NotImplementedError

    def import_data(self):
        if self.is_sqlite:
            file_exists = self.get_file_path()
            if not file_exists:
                return None

        # Set content type
        if self.content_type_model:
            self.content_type = ContentType.objects.get_for_model(
                self.content_type_model
            )

        conn = self.create_connection()
        with conn:
            self.select_table(conn)
            self.get_table_colums(conn)
            self.start_processing_rows()
            if self.max_row:
                self.max_row = int(self.max_row)
                rows = self.sqlite_rows[:self.max_row]
            else:
                rows = self.sqlite_rows
            index = 0
            for row in rows:
                print('Processing %s of %s\r' % (
                    index + 1,
                    len(rows)))
                self.current_row = row
                self.process_row(row, index)
                index += 1
            self.finish_processing_rows()
        conn.close()
        self.current_row = None


    def create_user_from_row(self, row, user_id=None):
        password_value = 'sha1${salt}${hash}'.format(
            salt=str(self.get_row_value('SaltValue', row)),
            hash=str(self.get_row_value('PasswordHash', row))
        )
        username_value = self.get_row_value('UserName', row).replace(
            ' ', '_').lower()
        date_joined = self.get_row_value('DateFrom', row)
        email_value = self.get_row_value('Email', row)
        if Profile.objects.filter(username=username_value).exists():
            profiles = Profile.objects.filter(username=username_value)
            if not profiles.filter(email=email_value).exists():
                same_username = len(profiles)
                username_value += '_%s' % str(same_username)
        profile, created = Profile.objects.get_or_create(
            username=username_value,
        )

        if created:
            profile.is_active = True
            profile.email = self.get_row_value('Email', row)
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

        if bims_created:
            bims_profile.qualifications = self.get_row_value('Qualifications')
            bims_profile.full_name = self.get_row_value('UserName')
            bims_profile.other = self.get_row_value('Other')
            bims_profile.data = {
                'PasswordHint': str(self.get_row_value('PasswordHint', row)),
                'RegionPolID': str(self.get_row_value('RegionPolID', row)),
                'OrganisationID': str(self.get_row_value(
                    'OrganisationID', row)),
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

        if not user_id:
            user_id = self.get_row_value('UserID', row)
        self.save_uuid(
            uuid=user_id,
            object_id=profile.id
        )
