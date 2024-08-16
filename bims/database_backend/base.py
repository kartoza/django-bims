import time

import django.db
from psycopg2 import InterfaceError, OperationalError
from django_tenants.postgresql_backend.base import (
    DatabaseWrapper as TenantDatabaseWrapper
)


class DatabaseWrapper(TenantDatabaseWrapper):
    def _cursor(self, name=None):
        try:
            return super()._cursor(name)
        except (OperationalError, InterfaceError) as e:
            if 'connection already closed' in str(e):
                self.close()
                self.connect()
                return super()._cursor(name)
            else:
                raise

    def connect(self):
        try:
            super().connect()
        except (OperationalError, InterfaceError):
            time.sleep(1)
            super().connect()

    def create_cursor(self, name=None):
        try:
            return super().create_cursor(name=name)
        except InterfaceError:
            django.db.close_old_connections()
            django.db.connection.connect()
            return super().create_cursor(name=name)
