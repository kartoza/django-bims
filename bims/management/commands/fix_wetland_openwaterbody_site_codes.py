from __future__ import annotations

import re
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

CORRECT_FORMAT_RE = re.compile(r'^[A-Za-z0-9]+-[A-Za-z0-9]+-\d{5}$')

UNSPECIFIED_CODE = 'UNSPECIFIED'
UNSPECIFIED_DISPLAY = 'unspecified'


class Command(BaseCommand):
    help = (
        "Check (dry-run) and fix Wetland and Open Waterbody location sites that "
        "use the River code format instead of the correct two-segment format, and "
        "ensure sites with no NWM6 name default to 'unspecified'."
    )

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
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[{label}] Dry run - no changes will be written.")
            )

        all_sites = LocationSite.objects.filter(
            ecosystem_type__iregex=r'^(wetland|open waterbody)$'
        ).order_by('id')

        total = all_sites.count()
        self.stdout.write(
            f"[{label}] Found {total} Wetland/Open Waterbody site(s) total."
        )

        if total == 0:
            return

        wrong_code_sites = []
        field_only_sites = []

        for site in all_sites:
            needs_regen = (
                not site.site_code or
                not CORRECT_FORMAT_RE.match(site.site_code)
            )
            needs_name_field = (
                not (site.wetland_name or '').strip() and
                not (site.user_wetland_name or '').strip()
            )

            if needs_regen:
                wrong_code_sites.append((site, needs_name_field))
            elif needs_name_field:
                field_only_sites.append(site)

        self.stdout.write(
            self.style.WARNING(
                f"[{label}] Wrong-format site code (River format used for "
                f"Wetland/OWB): {len(wrong_code_sites)}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"[{label}] Correct code but missing wetland_name field: "
                f"{len(field_only_sites)}"
            )
        )

        if not wrong_code_sites and not field_only_sites:
            self.stdout.write(self.style.SUCCESS(f"[{label}] No issues found."))
            return

        updated_code = 0
        updated_field = 0
        failed = 0

        signals.post_save.disconnect(location_site_post_save_handler)

        try:
            # --- Fix wrong-format site codes ---
            for index, (site, also_fix_field) in enumerate(wrong_code_sites, start=1):
                self.stdout.write(
                    f"[{label}] [{index}/{len(wrong_code_sites)}] "
                    f"id={site.pk} | {site.ecosystem_type} | "
                    f"current code: {site.site_code!r}"
                )

                try:
                    new_code = self._regenerate_code(site)
                except Exception as exc:
                    self.stderr.write(
                        self.style.ERROR(
                            f"[{label}]   Error generating code for site {site.pk}: {exc}"
                        )
                    )
                    failed += 1
                    continue

                self.stdout.write(
                    f"[{label}]   {site.site_code!r} -> {new_code!r}"
                    + (' [no change]' if site.site_code == new_code else '')
                )

                if not dry_run:
                    update_fields = ['site_code']
                    site.site_code = new_code

                    if also_fix_field:
                        site.wetland_name = UNSPECIFIED_DISPLAY
                        update_fields.append('wetland_name')
                        self.stdout.write(
                            f"[{label}]   wetland_name -> {UNSPECIFIED_DISPLAY!r}"
                        )

                    try:
                        with transaction.atomic():
                            site.save(update_fields=update_fields)
                        updated_code += 1
                    except Exception as exc:
                        self.stderr.write(
                            self.style.ERROR(
                                f"[{label}]   Failed to save site {site.pk}: {exc}"
                            )
                        )
                        failed += 1
                else:
                    if also_fix_field:
                        self.stdout.write(
                            f"[{label}]   wetland_name -> {UNSPECIFIED_DISPLAY!r}"
                        )
                    updated_code += 1

            # --- Fix field-only (code is fine, wetland_name is missing) ---
            for site in field_only_sites:
                self.stdout.write(
                    f"[{label}] id={site.pk} | {site.ecosystem_type} | "
                    f"wetland_name -> {UNSPECIFIED_DISPLAY!r}"
                )

                if not dry_run:
                    try:
                        site.wetland_name = UNSPECIFIED_DISPLAY
                        with transaction.atomic():
                            site.save(update_fields=['wetland_name'])
                        updated_field += 1
                    except Exception as exc:
                        self.stderr.write(
                            self.style.ERROR(
                                f"[{label}]   Failed to update site {site.pk}: {exc}"
                            )
                        )
                        failed += 1
                else:
                    updated_field += 1

        finally:
            signals.post_save.connect(location_site_post_save_handler)

        dry_prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"[{label}] {dry_prefix}Done. "
                f"Code fixed: {updated_code}, "
                f"Name field fixed: {updated_field}, "
                f"Failed: {failed}."
            )
        )

    def _regenerate_code(self, site: LocationSite) -> str:
        """
        Regenerate the site code for a wetland or open-waterbody site.

        Name resolution:
          Wetland: NWM6 name from additional_data (auto-used when 'wetlid' present)
            > user_wetland_name > 'UNSPECIFIED' (-> 'UNSP' in code).
          Open waterbody: legacy_river_name > river.name > 'UNSPECIFIED'.

        Routing:
          - Wetland: name goes via `wetland_name` kwarg.
          - Open waterbody: name goes via `river_name` kwarg because
            open_waterbody_catchment() uses that parameter.
        """
        lat = site.latitude
        lon = site.longitude

        if not lat or not lon:
            if site.geometry_point:
                lon, lat = site.geometry_point.x, site.geometry_point.y
            else:
                raise ValueError(f"Site {site.pk} has no coordinates.")

        ecosystem = site.ecosystem_type

        if ecosystem.lower() == 'wetland':
            # wetland_catchment() prefers additional_data['name'] (NWM6) when
            # additional_data contains 'wetlid'. Only supply wetland_name as
            # a fallback so we don't override valid NWM6 data.
            has_nwm6_name = bool(
                site.additional_data and
                'wetlid' in site.additional_data and
                site.additional_data.get('name')
            )
            wetland_name = (site.user_wetland_name or '').strip() or UNSPECIFIED_CODE
            new_code, _ = generate_site_code(
                location_site=site,
                lat=lat,
                lon=lon,
                ecosystem_type=ecosystem,
                wetland_name='' if has_nwm6_name else wetland_name,
            )
        else:
            # Open waterbody: open_waterbody_catchment() reads `river_name`.
            # Priority: legacy_river_name > river.name > UNSPECIFIED.
            owb_name = (
                (site.legacy_river_name or '').strip() or
                (site.river.name if site.river else '') or
                UNSPECIFIED_CODE
            )
            new_code, _ = generate_site_code(
                location_site=site,
                lat=lat,
                lon=lon,
                ecosystem_type=ecosystem,
                river_name=owb_name,
            )

        return new_code
