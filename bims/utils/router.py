import random
from django.conf import settings
from django.db import connections
from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_tenant_domain_model

PRIMARY = "default"


class ReadReplicaTenantMiddleware(TenantMainMiddleware):
    def process_request(self, request):
        # Connection needs first to be at the public schema, as this is where
        # the tenant metadata is stored.

        for con in connections:
            connections[con].set_schema_to_public()
        hostname = self.hostname_from_request(request)

        domain_model = get_tenant_domain_model()
        try:
            tenant = self.get_tenant(domain_model, hostname)
        except domain_model.DoesNotExist:
            return self.no_tenant_found(request, hostname)

        tenant.domain_url = hostname
        request.tenant = tenant
        for con in connections:
            connections[con].set_tenant(request.tenant)
        self.setup_url_routing(request)


DEFAULT_DB_ALIAS = 'default'


def extra_set_tenant_stuff(wrapper_class, tenant):
    if settings.REPLICA_ENV_VAR:
        chosen_db_key = random.choice(
            list(settings.DATABASES.keys())[1:])
    else:
        chosen_db_key = DEFAULT_DB_ALIAS
    try:
        database_name = wrapper_class.settings_dict["DATABASE"]
    except Exception:
        return
    try:
        connection_schema_name = connections.databases[chosen_db_key]['SCHEMA']
    except Exception:
        return
    if (
        database_name == DEFAULT_DB_ALIAS
        and connection_schema_name != tenant.schema_name
    ):
        try:
            tenant_replica_connection = connections[chosen_db_key]
            tenant_replica_connection.set_schema(tenant.schema_name)
        except Exception:  # noqa
            return


class CustomTenantMiddleware(TenantMainMiddleware):
    def process_request(self, request):
        super().process_request(request)
        if settings.REPLICA_ENV_VAR:
            for replica in list(settings.DATABASES.keys())[1:]:
                self._set_tenant_to_replicas(request, replica)

    def _set_tenant_to_replicas(self, request, alias: str) -> None:
        """
        Function in charge of setting the tenant on the
        read replica alias connection.
        :param request:
        :param alias str:
        :return None:
        """
        connection = connections.__getitem__(alias)
        if connection and hasattr(request, "tenant"):
            connection.set_tenant(request.tenant)


class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        """
        Reads go to a randomly-chosen replica.
        """
        if settings.REPLICA_ENV_VAR:
            available_databases = list(settings.DATABASES.keys())
            chosen_db_key = random.choice(available_databases)
            return chosen_db_key
        else:
            return PRIMARY

    def db_for_write(self, model, **hints):
        """
        Writes always go to primary.
        """
        return PRIMARY

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the primary/replica pool.
        """
        db_set = set(settings.DATABASES.keys())
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All non-auth models end up in this pool.
        """
        return True
