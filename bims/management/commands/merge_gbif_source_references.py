# coding=utf-8
"""
Tenant-aware command that merges GBIF SourceReferenceDatabase entries that
carry a URL on their DatabaseRecord into the canonical one (no URL).

Background: GBIF occurrences imported via per-download URLs historically
created a separate DatabaseRecord (and SourceReferenceDatabase) per download,
each with a URL.  The canonical record has no URL.  This command re-points
all related objects from the URL-bearing duplicates to the canonical one, then
deletes the duplicates.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger(__name__)

GBIF_NAME = "Global Biodiversity Information Facility (GBIF)"


class Command(BaseCommand):
    help = (
        "Merge GBIF SourceReferenceDatabase entries that have a URL into the "
        "canonical one (no URL) for each tenant."
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
            help="Process all tenants (default when no --schema-name is given).",
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
            help="Apply the merge.",
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

        mode = "DRY RUN" if dry_run else "LIVE -- records will be modified"
        self.stdout.write(f"{mode}: processing {len(tenants)} tenant(s).\n")

        for tenant in tenants:
            self.stdout.write(
                f"-- Tenant: {tenant.name} (schema: {tenant.schema_name})"
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
        from bims.models.source_reference import (
            SourceReference,
            SourceReferenceDatabase,
        )
        from django.contrib.contenttypes.fields import ForeignObjectRel

        # The canonical source reference: GBIF name, no URL on its DatabaseRecord.
        try:
            canonical = SourceReferenceDatabase.objects.get(
                source__name=GBIF_NAME,
                source__url__isnull=True,
                source_name=GBIF_NAME,
            )
        except SourceReferenceDatabase.DoesNotExist:
            try:
                canonical = SourceReferenceDatabase.objects.get(
                    source__name=GBIF_NAME,
                    source__url="",
                    source_name=GBIF_NAME,
                )
            except SourceReferenceDatabase.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        "  No canonical GBIF source reference (without URL) found. "
                        "Skipping."
                    )
                )
                return
        except SourceReferenceDatabase.MultipleObjectsReturned:
            self.stdout.write(
                self.style.WARNING(
                    "  Multiple canonical GBIF source references (without URL) found. "
                    "Manual review required. Skipping."
                )
            )
            return

        self.stdout.write(f"  Canonical source reference id={canonical.id}")

        # Duplicates: GBIF source references that DO have a URL.
        duplicates = SourceReferenceDatabase.objects.filter(
            source__name=GBIF_NAME,
        ).exclude(
            id=canonical.id,
        ).filter(
            source__url__isnull=False,
        ).exclude(
            source__url="",
        ).select_related("source")

        if not duplicates.exists():
            self.stdout.write("  No duplicate GBIF source references with a URL found.")
            return

        self.stdout.write(f"  Found {duplicates.count()} duplicate(s) to merge.")

        # Discover all reverse FK/M2M relations on SourceReference, excluding the
        # subclass proxy accessors to avoid re-assigning to the wrong polymorphic type.
        _excluded_accessors = {
            "sourcereferencebibliography",
            "sourcereferencedatabase",
            "sourcereferencedocument",
        }
        links = [
            rel.get_accessor_name()
            for rel in SourceReference._meta.get_fields()
            if issubclass(type(rel), ForeignObjectRel)
            and rel.get_accessor_name() not in _excluded_accessors
        ]

        merged_count = 0
        deleted_source_count = 0
        deleted_ref_count = 0
        doi_updated_count = 0

        for duplicate in duplicates.iterator():
            url = duplicate.source.url if duplicate.source else "(no source)"
            self.stdout.write(f"  Processing duplicate id={duplicate.id} url={url}")

            # If the URL is a DOI, stamp it on linked collection records that
            # have no doi yet before re-pointing them to the canonical reference.
            is_doi_url = duplicate.source and duplicate.source.url and "doi.org" in duplicate.source.url
            if is_doi_url:
                from bims.models.biological_collection_record import BiologicalCollectionRecord
                doi_candidates = BiologicalCollectionRecord.objects.filter(
                    source_reference=duplicate,
                ).filter(
                    models.Q(doi="") | models.Q(doi__isnull=True)
                )
                doi_count = doi_candidates.count()
                if doi_count:
                    if dry_run:
                        self.stdout.write(
                            f"    [DRY RUN] {doi_count} collection record(s) would get "
                            f"doi={duplicate.source.url}"
                        )
                    else:
                        updated = doi_candidates.update(doi=duplicate.source.url)
                        doi_updated_count += updated
                        self.stdout.write(
                            f"    Set doi={duplicate.source.url} on {updated} collection record(s)"
                        )

            related_totals = {}
            for link in links:
                try:
                    objects = getattr(duplicate, link).all()
                    count = objects.count()
                    if count > 0:
                        related_totals[link] = count
                except Exception as exc:
                    logger.debug("Skipping relation %s: %s", link, exc)
                    continue

            if related_totals:
                for link, count in related_totals.items():
                    self.stdout.write(
                        f"    {link}: {count} record(s) would be re-pointed"
                        if dry_run
                        else f"    {link}: re-pointing {count} record(s)"
                    )

            if not dry_run:
                for link in links:
                    try:
                        objects = getattr(duplicate, link).all()
                        if objects.count() > 0:
                            field_name = getattr(duplicate, link).field.name
                            objects.update(**{field_name: canonical})
                    except Exception as exc:
                        logger.warning("Could not re-point relation %s: %s", link, exc)
                        continue

                # Delete the per-download DatabaseRecord, then the source reference.
                source = duplicate.source
                duplicate.delete()
                deleted_ref_count += 1
                if source and source.id != (canonical.source_id if canonical.source else None):
                    source.delete()
                    deleted_source_count += 1

            merged_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"  [DRY RUN] Would merge {merged_count} duplicate(s) into "
                    f"canonical id={canonical.id}."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Merged {merged_count} duplicate(s) into canonical "
                    f"id={canonical.id}. Deleted {deleted_ref_count} source reference(s) "
                    f"and {deleted_source_count} DatabaseRecord(s). "
                    f"Set doi on {doi_updated_count} collection record(s)."
                )
            )
