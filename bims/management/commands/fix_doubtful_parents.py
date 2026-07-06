# coding=utf-8
"""Populate the parent reference for doubtful taxa.

Doubtful taxa are treated like accepted taxa: they keep their own parent
hierarchy (unlike synonyms, which point to an accepted taxon). This command
finds doubtful taxa that are missing a parent and, when a GBIF key is
available, resolves the parent straight from GBIF.
"""

import sys

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:  # pragma: no cover - tenant support optional
    get_tenant_model = None
    schema_context = None

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# Top-level ranks are not expected to have a parent.
TOP_LEVEL_RANKS = ['DOMAIN', 'KINGDOM', 'Domain', 'Kingdom']


class Command(BaseCommand):
    help = (
        "Fix the parent reference for doubtful taxa. When a GBIF key is "
        "present, the parent is pulled from GBIF. Supports multi-tenant "
        "deployments via --tenant/--all-tenants."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant",
            dest="tenant",
            default=None,
            help="Tenant schema name to run against.",
        )
        parser.add_argument(
            "--all-tenants",
            dest="all_tenants",
            action="store_true",
            default=False,
            help="Iterate through every tenant schema (excludes public).",
        )
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            default=False,
            help="Report what would be fixed without saving.",
        )

    def handle(self, *args, **options):
        schema = options.get("tenant")
        all_tenants = options.get("all_tenants")

        if schema and all_tenants:
            raise CommandError("Use either --tenant or --all-tenants, not both.")

        if schema:
            self._run_for_schema(schema, options)
            return

        if all_tenants:
            if schema_context is None or get_tenant_model is None:
                raise CommandError("django-tenants is required for tenant iteration.")

            TenantModel = get_tenant_model()
            tenants_qs = TenantModel.objects.exclude(schema_name="public")
            if not tenants_qs.exists():
                self.stdout.write(self.style.WARNING("No tenant schemas found."))
                return

            for tenant in tenants_qs:
                self._run_fix_in_schema(tenant.schema_name, options)
            return

        # Default to current schema
        self.stdout.write(self.style.HTTP_INFO("Running in current schema"))
        self._fix(options)

    def _run_for_schema(self, schema_name: str, options):
        if schema_context is None or get_tenant_model is None:
            self.stderr.write("This command requires django-tenants but it is not available.")
            sys.exit(1)

        tenant = self._get_tenant(schema_name)
        if not tenant:
            sys.exit(1)

        self._run_fix_in_schema(tenant.schema_name, options)

    def _run_fix_in_schema(self, schema_name: str, options):
        with schema_context(schema_name):
            self.stdout.write(self.style.HTTP_INFO(f"Running in tenant schema: {schema_name}"))
            self._fix(options)

    def _fix(self, options):
        from bims.models import Taxonomy

        dry_run = options.get("dry_run", False)

        qs = (
            Taxonomy.objects.filter(
                taxonomic_status__iexact="DOUBTFUL",
                parent__isnull=True,
            )
            .exclude(rank__in=TOP_LEVEL_RANKS)
        )

        total = qs.count()
        if not total:
            self.stdout.write(self.style.SUCCESS("No doubtful taxa missing a parent."))
            return

        self.stdout.write(
            self.style.HTTP_INFO(f"Found {total} doubtful taxa missing a parent.")
        )

        fixed = 0
        skipped_no_key = 0
        skipped_no_parent = 0

        for taxon in qs.iterator():
            if not taxon.gbif_key:
                skipped_no_key += 1
                self.stdout.write(
                    f"  - {taxon.canonical_name} (ID {taxon.pk}): no GBIF key, skipping."
                )
                continue

            parent_key = self._resolve_parent_key(taxon)
            if not parent_key:
                skipped_no_parent += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  - {taxon.canonical_name} (ID {taxon.pk}): "
                        f"no parent key found on GBIF (key {taxon.gbif_key})."
                    )
                )
                continue

            if dry_run:
                fixed += 1
                self.stdout.write(
                    f"  [dry-run] {taxon.canonical_name} (ID {taxon.pk}) "
                    f"-> parent GBIF key {parent_key}"
                )
                continue

            parent = self._fetch_parent(parent_key)
            if not parent:
                skipped_no_parent += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  - {taxon.canonical_name} (ID {taxon.pk}): "
                        f"could not fetch parent {parent_key} from GBIF."
                    )
                )
                continue

            with transaction.atomic():
                taxon.parent = parent
                taxon.save(update_fields=["parent"])

            fixed += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  - {taxon.canonical_name} (ID {taxon.pk}) "
                    f"-> parent {parent.canonical_name} (ID {parent.pk})"
                )
            )

        prefix = "[dry-run] Would fix" if dry_run else "Fixed"
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix} {fixed} doubtful taxa. "
                f"Skipped {skipped_no_key} without a GBIF key and "
                f"{skipped_no_parent} with no resolvable parent."
            )
        )

    def _resolve_parent_key(self, taxon):
        """Return the GBIF parent key for a doubtful taxon (read-only)."""
        from bims.utils.gbif import get_species

        parent_key = None
        gbif_data = taxon.gbif_data if isinstance(taxon.gbif_data, dict) else None
        if gbif_data:
            parent_key = gbif_data.get("parentKey")

        if not parent_key:
            species_data = get_species(taxon.gbif_key)
            if isinstance(species_data, dict):
                parent_key = species_data.get("parentKey")

        if not parent_key or parent_key == taxon.gbif_key:
            return None

        return parent_key

    def _fetch_parent(self, parent_key):
        """Materialize and return the parent Taxonomy for a GBIF key."""
        from bims.utils.fetch_gbif import fetch_all_species_from_gbif

        return fetch_all_species_from_gbif(
            gbif_key=parent_key,
            fetch_children=False,
        )

    def _get_tenant(self, schema_name):
        TenantModel = get_tenant_model()
        try:
            return TenantModel.objects.get(schema_name=schema_name)
        except TenantModel.DoesNotExist:
            self.stderr.write(f"Tenant with schema '{schema_name}' not found.")
            return None
