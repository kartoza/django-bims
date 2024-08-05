import django.db
from psycopg2 import InterfaceError
from django_tenants.postgresql_backend.base import (
    DatabaseWrapper as TenantDatabaseWrapper
)


class DatabaseWrapper(TenantDatabaseWrapper):
    def create_cursor(self, name=None):
        try:
            return super().create_cursor(name=name)
        except InterfaceError:
            django.db.close_old_connections()
            django.db.connection.connect()
            return super().create_cursor(name=name)
