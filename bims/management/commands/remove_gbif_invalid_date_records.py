# coding=utf-8
"""
Tenant-aware management command that finds and optionally removes
BiologicalCollectionRecord entries sourced from GBIF that carry the
RECORDED_DATE_INVALID quality flag in their additional_data.

Two locations are checked inside additional_data:
  - "issues"      – key used by the old GBIF API harvester
  - "gbif_issues" – key used by the updated DwC-archive harvester
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger(__name__)

RECORDED_DATE_INVALID = 'RECORDED_DATE_INVALID'
GBIF_SOURCE_COLLECTION = 'gbif'


class Command(BaseCommand):
    help = (
        "Find (and optionally remove) GBIF collection records flagged with "
        "RECORDED_DATE_INVALID in additional_data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-s", "--schema-name",
            dest="schema_names",
            action="append",
            help="Limit to specific tenant schema(s). May be repeated.",
        )
        parser.add_argument(
            "--all-tenants",
            action="store_true",
            help="Process all tenants (default when no --schema-name given).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=True,
            help="Report what would be removed without touching the database (default: True).",
        )
        parser.add_argument(
            "--no-dry-run",
            dest="dry_run",
            action="store_false",
            help="Actually delete the flagged records.",
        )

    def handle(self, *args, **options):
        schema_names = options.get("schema_names") or []
        all_tenants = options.get("all_tenants", False)
        dry_run = options.get("dry_run", True)

        if schema_names and all_tenants:
            raise CommandError("Use either --schema-name or --all-tenants, not both.")

        tenants = self._get_tenants(schema_names)
        if not tenants:
            self.stdout.write(self.style.WARNING("No tenants found."))
            return

        mode = "DRY RUN" if dry_run else "LIVE — records will be deleted"
        self.stdout.write(f"{mode}: processing {len(tenants)} tenant(s).\n")

        for tenant in tenants:
            self.stdout.write(
                f"── Tenant: {tenant.name} (schema: {tenant.schema_name})"
            )
            with tenant_context(tenant):
                if dry_run:
                    self._process_tenant(dry_run=True)
                else:
                    with transaction.atomic():
                        self._process_tenant(dry_run=False)

        self.stdout.write(self.style.SUCCESS("\nDone."))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_tenants(self, schema_names):
        Tenant = get_tenant_model()
        qs = Tenant.objects.exclude(schema_name="public")
        if schema_names:
            qs = qs.filter(schema_name__in=schema_names)
            missing = set(schema_names) - set(qs.values_list("schema_name", flat=True))
            if missing:
                raise CommandError(
                    f"Tenant schema(s) not found: {', '.join(sorted(missing))}"
                )
        return list(qs.order_by("schema_name"))

    def _build_queryset(self):
        """Return a QS of flagged GBIF records for the active tenant schema."""
        from bims.models.biological_collection_record import BiologicalCollectionRecord

        return (
            BiologicalCollectionRecord.objects
            .filter(source_collection__iexact=GBIF_SOURCE_COLLECTION)
            .filter(
                # Old harvester stored issues under "issues" key
                Q(additional_data__issues__contains=[RECORDED_DATE_INVALID])
                # New DwC-archive harvester stores under "gbif_issues" key
                | Q(additional_data__gbif_issues__contains=[RECORDED_DATE_INVALID])
            )
        )

    def _process_tenant(self, dry_run):
        qs = self._build_queryset()
        total = qs.count()

        self.stdout.write(f"  Flagged records found: {total}")

        if total == 0:
            return

        if dry_run:
            self.stdout.write("  [DRY RUN] Records that would be removed:")
            for rec in qs.values("id", "upstream_id", "collection_date", "taxonomy__canonical_name").iterator(chunk_size=500):
                self.stdout.write(
                    f"    pk={rec['id']}  gbifID={rec['upstream_id']}  "
                    f"date={rec['collection_date']}  "
                    f"taxon={rec['taxonomy__canonical_name']}"
                )
            return

        deleted_count, _ = qs.delete()
        self.stdout.write(
            self.style.SUCCESS(f"  Deleted {deleted_count} record(s).")
        )
