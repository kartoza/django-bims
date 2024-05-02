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


def extra_set_tenant_stuff(wrapper_class, tenant):
    try:
        tenant_replica_connection = connections["replica_1"]
    except Exception:  # noqa
        return
    if (
            wrapper_class.settings_dict["DATABASE"] == "default"
            and tenant_replica_connection.schema_name != tenant.schema_name
    ):
        tenant_replica_connection.set_schema(tenant.schema_name)
        print(f"changing replica schema to {tenant.schema_name}")


class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        """
        Reads go to a randomly-chosen replica.
        """
        if settings.REPLICA_ENV_VAR:
            chosen_replica_key = random.choice(
                list(settings.DATABASES.keys())[1:])
            return chosen_replica_key
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
