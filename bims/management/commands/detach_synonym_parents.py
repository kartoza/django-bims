# coding=utf-8
"""Detach parents from synonym and doubtful taxa."""

import sys

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:  # pragma: no cover - tenant support optional
    get_tenant_model = None
    schema_context = None

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q


class Command(BaseCommand):
    help = (
        "Ensure synonym and doubtful taxa do not have parent references. "
        "Supports multi-tenant deployments via --tenant/--all-tenants."
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
            help="Report how many records would be updated without saving.",
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
                self._run_detach_in_schema(tenant.schema_name, options)
            return

        # Default to current schema
        self.stdout.write(self.style.HTTP_INFO("Running in current schema"))
        self._detach(options)

    def _run_for_schema(self, schema_name: str, options):
        if schema_context is None or get_tenant_model is None:
            self.stderr.write("This command requires django-tenants but it is not available.")
            sys.exit(1)

        tenant = self._get_tenant(schema_name)
        if not tenant:
            sys.exit(1)

        self._run_detach_in_schema(tenant.schema_name, options)

    def _run_detach_in_schema(self, schema_name: str, options):
        with schema_context(schema_name):
            self.stdout.write(self.style.HTTP_INFO(f"Running in tenant schema: {schema_name}"))
            self._detach(options)

    def _detach(self, options):
        from bims.models import Taxonomy

        dry_run = options.get("dry_run", False)

        qs = Taxonomy.objects.filter(
            Q(taxonomic_status__iexact="DOUBTFUL")
            | Q(taxonomic_status__icontains="SYNONYM")
        ).exclude(parent__isnull=True)

        to_update = qs.count()
        if not to_update:
            self.stdout.write(self.style.SUCCESS("No synonym/doubtful taxa with parents found."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[dry-run] Would detach {to_update} synonym/doubtful taxa from parents."
                )
            )
            return

        with transaction.atomic():
            updated = qs.update(parent=None)

        self.stdout.write(
            self.style.SUCCESS(
                f"Detached {updated} synonym/doubtful taxa from their parents."
            )
        )

    def _get_tenant(self, schema_name):
        TenantModel = get_tenant_model()
        try:
            return TenantModel.objects.get(schema_name=schema_name)
        except TenantModel.DoesNotExist:
            self.stderr.write(f"Tenant with schema '{schema_name}' not found.")
            return None
