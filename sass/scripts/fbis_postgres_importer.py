import psycopg2 as driv
from sass.scripts.fbis_importer import FbisImporter


class FbisPostgresImporter(FbisImporter):

    is_sqlite = False

    def create_connection(self):
        try:
            conn = driv.connect(database=self.postgres_database,
                                user=self.postgres_user,
                                password=self.postgres_password,
                                host=self.postgres_host,
                                port=self.postgres_port)
            return conn
        except driv.OperationalError as e:
            print(e)
        return None

    def process_row(self, row, index):
        raise NotImplementedError

    @property
    def content_type_model(self):
        raise NotImplementedError

    @property
    def table_name(self):
        raise NotImplementedError
