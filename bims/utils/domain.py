from django.contrib.sites.models import Site
from django.db import connection
from tenants.models import (
    Domain,
    Client
)


def get_current_domain():
    schema_name = connection.schema_name
    try:
        tenant = Client.objects.get(
            schema_name=schema_name
        )
        return tenant.domains.first().domain
    except Client.DoesNotExist:
        return Site.objects.get_current().domain
