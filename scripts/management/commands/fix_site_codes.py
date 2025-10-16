from __future__ import annotations

import sys

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.db.models import signals

from bims.models import LocationSite, location_site_post_save_handler, generate_site_code

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None


class Command(BaseCommand):
    """
    Update location sites to use legacy-style site codes if they do not match the expected format.
    Optionally supports multi-tenant schemas via --tenant.
    """

    help = "Update LocationSite.site_code to match legacy format for unmatched entries."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--tenant",
            metavar="SCHEMA",
            help="Target schema name when using django-tenants. If omitted, runs in current schema.",
        )

    def handle(self, *args, **options) -> None:
        schema = options.get("tenant")

        if schema:
            if schema_context is None:
                self.stderr.write(
                    self.style.ERROR("This command requires django-tenants but it is not available.")
                )
                sys.exit(1)

            tenant = self._get_tenant(schema)
            if not tenant:
                sys.exit(1)

            with schema_context(tenant.schema_name):
                self.stdout.write(self.style.HTTP_INFO(f"Running in tenant schema: {schema}"))
                self._run_update(label=f"tenant '{schema}'")
        else:
            self.stdout.write(self.style.HTTP_INFO("Running in current schema"))
            self._run_update(label="current schema")

    def _run_update(self, label: str) -> None:
        location_sites = LocationSite.objects.exclude(
            site_code__iregex=r'^[A-Za-z0-9]{1,6}-[A-Za-z0-9]*$'
        )
        count = location_sites.count()
        self.stdout.write(self.style.WARNING(f"[{label}] Found {count} site(s) to update."))

        if count == 0:
            return

        signals.post_save.disconnect(location_site_post_save_handler)

        updated = 0
        for index, location_site in enumerate(location_sites, start=1):
            self.stdout.write(f"[{label}] Processing {index} of {count} (id={location_site.pk})")
            try:
                location_site.site_code, _ = generate_site_code(
                    location_site=location_site,
                    lat=location_site.latitude,
                    lon=location_site.longitude,
                )
                with transaction.atomic():
                    location_site.save()
                updated += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f"[{label}] Failed to update LocationSite {location_site.pk}: {e}"
                ))

        signals.post_save.connect(location_site_post_save_handler)

        self.stdout.write(self.style.SUCCESS(f"[{label}] Completed. {updated} site(s) updated."))

    def _get_tenant(self, schema_name):
        Tenant = get_tenant_model()
        try:
            return Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Tenant with schema '{schema_name}' not found.")
            )
            return None
