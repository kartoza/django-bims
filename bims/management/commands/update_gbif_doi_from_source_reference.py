# coding=utf-8
"""
Tenant-aware management command that backfills the ``doi`` field on
BiologicalCollectionRecord from legacy GBIF SourceReferenceDatabase entries
that stored a per-download URL on their DatabaseRecord.

After the migration to storing DOIs directly on the occurrence, each
SourceReferenceDatabase for GBIF should have no URL.  This command copies
the URL from any such source reference to the record's ``doi`` field and
can optionally clear the URL from the DatabaseRecord afterwards.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger(__name__)

GBIF_NAME = "Global Biodiversity Information Facility (GBIF)"


class Command(BaseCommand):
    help = (
        "Backfill the doi field on BiologicalCollectionRecord from GBIF "
        "SourceReferenceDatabase entries that carry a per-download URL."
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
            help="Report what would change without touching the database (default: True).",
        )
        parser.add_argument(
            "--no-dry-run",
            dest="dry_run",
            action="store_false",
            help="Apply the updates.",
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

        mode = "DRY RUN" if dry_run else "LIVE — records will be updated"
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

    def _process_tenant(self, dry_run):
        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.models.source_reference import SourceReferenceDatabase

        gbif_source_refs = (
            SourceReferenceDatabase.objects
            .filter(source__name=GBIF_NAME)
            .exclude(source__url="")
            .exclude(source__url__isnull=True)
            .select_related("source")
        )

        if not gbif_source_refs.exists():
            self.stdout.write("  No GBIF source references with a URL found.")
            return

        total_updated = 0

        for source_ref in gbif_source_refs.iterator():
            doi_url = source_ref.source.url
            records = BiologicalCollectionRecord.objects.filter(
                source_reference=source_ref,
                doi="",
            )
            count = records.count()
            if count == 0:
                continue

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] {count} record(s) would get doi={doi_url}"
                    f"  (source_reference id={source_ref.id})"
                )
            else:
                updated = records.update(doi=doi_url)
                total_updated += updated
                self.stdout.write(
                    f"  Updated {updated} record(s) with doi={doi_url}"
                    f"  (source_reference id={source_ref.id})"
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"  Total records updated: {total_updated}")
            )
