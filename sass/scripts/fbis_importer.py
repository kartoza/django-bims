import os
import sqlite3
from sqlite3 import Error
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from bims.models.fbis_uuid import FbisUUID


class FbisImporter(object):

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

    def get_object_from_uuid(self, column, model):
        content_object = None
        if not self.current_row:
            return None
        ctype = ContentType.objects.get_for_model(model)
        objects = FbisUUID.objects.filter(
            uuid=self.get_row_value(column, self.current_row),
            content_type=ctype
        )
        if objects.exists():
            content_object = objects[0].content_object
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
        cur.execute('SELECT * FROM {table_name}'.format(
            table_name=self.table_name.upper()
        ))
        self.sqlite_rows = cur.fetchall()
        cur.close()

    def get_table_colums(self, conn):
        cur = conn.cursor()
        cur.execute('SELECT * FROM {table_name} WHERE 1=0;'.format(
            table_name=self.table_name.upper()
        ))
        self.table_colums = [d[0] for d in cur.description]
        cur.close()

    def save_uuid(self, uuid, object_id):
        if not self.content_type:
            print('Empty content type')
            return
        fbis_uuid, uuid_created = FbisUUID.objects.get_or_create(
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
        column_index = self.table_colums.index(column_name)
        if column_index < 0:
            return None
        if not row[column_index]:
            if return_none_if_empty:
                return None
            return ''
        else:
            return row[column_index]

    @property
    def content_type_model(self):
        raise NotImplementedError

    @property
    def table_name(self):
        raise NotImplementedError

    def import_data(self):
        file_exists = self.get_file_path()
        if not file_exists:
            return None

        # Set content type
        self.content_type = ContentType.objects.get_for_model(
            self.content_type_model
        )

        conn = self.create_connection()
        with conn:
            self.select_table(conn)
            self.get_table_colums(conn)
            self.start_processing_rows()
            if self.max_row:
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
