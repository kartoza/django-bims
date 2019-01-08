import os
import pandas_access as mdb
from pandas.core.frame import DataFrame
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from bims.models.fbis_uuid import FbisUUID


class FbisImporter(object):

    def __init__(self, accdb_filename, max_row = None):
        self.accdb_filename = accdb_filename
        self.accdb_filepath = None
        self.accdb_rows = None
        self.max_row = max_row
        self.content_type = None

    def get_file_path(self):
        self.accdb_filepath = os.path.join(
            settings.MEDIA_ROOT,
            self.accdb_filename
        )
        if not os.path.isfile(self.accdb_filepath):
            print('%s not found in media directory' % self.accdb_filename)
            return False
        return True

    def save_uuid(self, uuid, object_id):
        if not self.content_type:
            print('Empty content type')
            return
        fbis_uuid, uuid_created = FbisUUID.objects.get_or_create(
            content_type=self.content_type,
            object_id=object_id,
            uuid=uuid
        )

    def process_row(self, index):
        raise NotImplementedError

    def get_row_value(self, index, column):
        if not isinstance(self.accdb_rows, DataFrame):
            return None
        if column not in self.accdb_rows:
            return None
        if index not in self.accdb_rows[column]:
            return None
        return self.accdb_rows[column][index]

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

        # Read table.
        df = mdb.read_table(
            rdb_file=self.accdb_filepath,
            table_name=self.table_name,
            promote='nullable_int_to_float')

        if self.max_row:
            _max_row = self.max_row
        else:
            _max_row = len(df)

        self.accdb_rows = df.head(_max_row)
        for i in range(len(self.accdb_rows)):
            self.process_row(i)
