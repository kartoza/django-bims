from __future__ import annotations

import sys

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import signals

from bims.models import LocationSite, location_site_post_save_handler, generate_site_code

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None

ECOSYSTEM_TYPES = ('wetland', 'open waterbody')


class Command(BaseCommand):
    help = "Regenerate site codes for Wetland and Open Waterbody location sites."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--tenant",
            metavar="SCHEMA",
            help=(
                "Target schema name when using django-tenants. "
                "If omitted, runs in the current schema."
            ),
        )
        parser.add_argument(
            "--all-tenants",
            action="store_true",
            help="Run against all non-public tenant schemas.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without writing to the database.",
        )

    def handle(self, *args, **options) -> None:
        schema = options.get("tenant")
        all_tenants = options.get("all_tenants", False)
        dry_run = options.get("dry_run", False)

        if schema and all_tenants:
            self.stderr.write(
                self.style.ERROR("Use either --tenant or --all-tenants, not both.")
            )
            sys.exit(1)

        if schema or all_tenants:
            if schema_context is None or get_tenant_model is None:
                self.stderr.write(
                    self.style.ERROR(
                        "This command requires django-tenants but it is not installed."
                    )
                )
                sys.exit(1)

            tenants = self._get_tenants(schema)
            if not tenants:
                self.stderr.write(self.style.ERROR("No matching tenant(s) found."))
                sys.exit(1)

            for tenant in tenants:
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f"Running in tenant schema: {tenant.schema_name}"
                    )
                )
                with schema_context(tenant.schema_name):
                    self._run(label=f"tenant '{tenant.schema_name}'", dry_run=dry_run)
        else:
            self.stdout.write(self.style.HTTP_INFO("Running in current schema"))
            self._run(label="current schema", dry_run=dry_run)

    def _get_tenants(self, schema_name: str | None):
        Tenant = get_tenant_model()
        qs = Tenant.objects.exclude(schema_name="public")
        if schema_name:
            qs = qs.filter(schema_name=schema_name)
        return list(qs.order_by("schema_name"))

    def _run(self, label: str, dry_run: bool) -> None:
        sites = LocationSite.objects.filter(
            ecosystem_type__iregex=r'^(wetland|open waterbody)$'
        )
        count = sites.count()
        self.stdout.write(
            self.style.WARNING(
                f"[{label}] Found {count} site(s) with ecosystem type "
                f"Wetland or Open Waterbody."
            )
        )

        if count == 0:
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[{label}] Dry run — no changes will be written.")
            )

        signals.post_save.disconnect(location_site_post_save_handler)

        updated = 0
        failed = 0

        try:
            for index, site in enumerate(sites, start=1):
                self.stdout.write(
                    f"[{label}] Processing {index}/{count} "
                    f"(id={site.pk}, ecosystem_type={site.ecosystem_type})"
                )

                wetland_name = ''
                if (
                    site.ecosystem_type.lower() == 'wetland'
                    and site.additional_data
                    and 'wetland_name' in site.additional_data
                ):
                    wetland_name = site.additional_data.get('wetland_name', '')

                river_name = site.legacy_river_name or (
                    site.river.name if site.river else ''
                )

                try:
                    new_site_code, _ = generate_site_code(
                        location_site=site,
                        lat=site.latitude,
                        lon=site.longitude,
                        river_name=river_name,
                        ecosystem_type=site.ecosystem_type,
                        wetland_name=wetland_name,
                    )
                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(
                            f"[{label}] Error generating site code for "
                            f"LocationSite {site.pk}: {e}"
                        )
                    )
                    failed += 1
                    continue

                if site.site_code == new_site_code:
                    self.stdout.write(
                        f"[{label}]   Unchanged: {site.site_code}"
                    )
                    continue

                self.stdout.write(
                    f"[{label}]   {site.site_code!r} -> {new_site_code!r}"
                )

                if not dry_run:
                    try:
                        with transaction.atomic():
                            site.site_code = new_site_code
                            site.save()
                        updated += 1
                    except Exception as e:
                        self.stderr.write(
                            self.style.ERROR(
                                f"[{label}] Failed to save LocationSite {site.pk}: {e}"
                            )
                        )
                        failed += 1
                else:
                    updated += 1
        finally:
            signals.post_save.connect(location_site_post_save_handler)

        dry_prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"[{label}] {dry_prefix}Done. "
                f"{updated} site(s) updated, {failed} failed."
            )
        )
