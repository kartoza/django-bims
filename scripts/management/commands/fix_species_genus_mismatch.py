# -*- coding: utf-8 -*-
"""
Management command to detect and fix species/subspecies whose genus name does
not match their parent taxon's genus, by re-fetching data from GBIF.

Rules:
  - SPECIES:    first word of canonical_name must match parent.canonical_name
                (parent is a genus taxon, e.g. "Ammannia")
  - SUBSPECIES: first word of canonical_name must match first word of
                parent.canonical_name (parent is a species, e.g. "Ammannia baccifera")
  - NO PARENT:  accepted taxa (any rank except kingdom) with no parent taxon
                are also flagged as candidates to fix.

Usage:
    python manage.py fix_species_genus_mismatch
    python manage.py fix_species_genus_mismatch --dry-run
    python manage.py fix_species_genus_mismatch --tenant myschema
    python manage.py fix_species_genus_mismatch --tenant myschema --dry-run
"""
from __future__ import annotations

import sys
import logging

from django.core.management.base import BaseCommand

from bims.enums.taxonomic_rank import TaxonomicRank
from bims.enums.taxonomic_status import TaxonomicStatus
from bims.models import Taxonomy

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Find species/subspecies whose genus name (first word of canonical_name) does not match "
        "their parent taxon's genus, and accepted taxa (non-kingdom) that have no parent, "
        "then fix them by re-fetching from GBIF."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--tenant",
            metavar="SCHEMA",
            help="Target schema name when using django-tenants. If omitted, runs in current schema.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Report mismatches without making any changes.",
        )

    def handle(self, *args, **options) -> None:
        schema = options.get("tenant")
        self.dry_run = options["dry_run"]

        if self.dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE: no changes will be made ---"))

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
                self._run(label=f"tenant '{schema}'")
        else:
            self.stdout.write(self.style.HTTP_INFO("Running in current schema"))
            self._run(label="current schema")

    def _run(self, label: str) -> None:
        qs = Taxonomy.objects.filter(
            rank__in=[TaxonomicRank.SPECIES.name, TaxonomicRank.SUBSPECIES.name, TaxonomicRank.VARIETY.name],
            parent__isnull=False,
            taxonomic_status=TaxonomicStatus.ACCEPTED.name
        ).select_related("parent")

        no_parent_qs = Taxonomy.objects.filter(
            taxonomic_status=TaxonomicStatus.ACCEPTED.name,
            parent__isnull=True,
        ).exclude(rank=TaxonomicRank.KINGDOM.name)

        total = qs.count()
        total_no_parent = no_parent_qs.count()
        self.stdout.write(
            f"[{label}] Checking {total} species/subspecies taxa for genus mismatch "
            f"and {total_no_parent} accepted taxa for missing parent..."
        )

        # Each candidate: (taxon, genus_from_name, expected_genus, parent_canonical, reason)
        candidates = []
        for taxon in qs.iterator():
            genus_from_name = self._extract_genus(taxon.canonical_name)
            parent_canonical = (taxon.parent.canonical_name or "").strip()

            if not parent_canonical:
                continue

            # For subspecies/variety the parent is a species (e.g. "Ammannia baccifera"),
            # so we compare against the genus portion (first word) of the parent.
            # For species the parent is a genus taxon, so we compare the full name.
            if taxon.rank in [TaxonomicRank.SUBSPECIES.name, TaxonomicRank.VARIETY.name]:
                expected_genus = self._extract_genus(parent_canonical)
            else:
                expected_genus = parent_canonical

            if genus_from_name.lower() != expected_genus.lower():
                candidates.append((taxon, genus_from_name, expected_genus, parent_canonical, "genus mismatch"))
                continue

            if taxon == taxon.parent:
                candidates.append((taxon, genus_from_name, expected_genus, parent_canonical, "self-referencing parent"))

        for taxon in no_parent_qs.iterator():
            candidates.append((
                taxon,
                self._extract_genus(taxon.canonical_name),
                "",
                "",
                "no parent",
            ))

        self.stdout.write(
            self.style.WARNING(f"[{label}] Found {len(candidates)} candidate(s) to fix.")
        )

        fixed = 0
        skipped_no_gbif = 0

        for taxon, genus_from_name, expected_genus, parent_canonical, reason in candidates:
            self.stdout.write(
                f"  {reason.upper()} [{taxon.rank}] id={taxon.pk} | "
                f"canonical_name='{taxon.canonical_name}' | "
                f"genus_from_name='{genus_from_name}' | "
                f"expected_genus='{expected_genus}' | "
                f"parent='{parent_canonical}' | "
                f"gbif_key={taxon.gbif_key}"
            )

            if not taxon.gbif_key:
                self.stdout.write(
                    self.style.WARNING(
                        f"    -> Skipping id={taxon.pk}: no gbif_key, cannot re-fetch."
                    )
                )
                skipped_no_gbif += 1
                continue

            if self.dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"    -> [DRY RUN] Would re-fetch from GBIF (gbif_key={taxon.gbif_key})."
                    )
                )
                fixed += 1
                continue

            try:
                from bims.utils.fetch_gbif import fetch_all_species_from_gbif
                self.stdout.write(
                    f"    -> Re-fetching from GBIF (gbif_key={taxon.gbif_key})..."
                )
                fetch_all_species_from_gbif(
                    species=taxon.scientific_name,
                    gbif_key=taxon.gbif_key,
                    fetch_vernacular_names=True,
                )
                fixed += 1
                self.stdout.write(
                    self.style.SUCCESS(f"    -> Done for id={taxon.pk}.")
                )
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"    -> Failed for id={taxon.pk}: {exc}")
                )
                logger.exception("Error re-fetching GBIF data for taxon id=%s", taxon.pk)

        action = "Would fix" if self.dry_run else "Fixed"
        self.stdout.write(
            self.style.SUCCESS(
                f"[{label}] Complete. {action} {fixed}, skipped (no gbif_key) {skipped_no_gbif}."
            )
        )

    @staticmethod
    def _extract_genus(canonical_name: str) -> str:
        """Return the first word of a canonical name (i.e. the genus part)."""
        if not canonical_name:
            return ""
        return canonical_name.strip().split()[0]

    def _get_tenant(self, schema_name: str):
        Tenant = get_tenant_model()
        try:
            return Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Tenant with schema '{schema_name}' not found.")
            )
            return None
