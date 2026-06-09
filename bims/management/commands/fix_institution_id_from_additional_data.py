# coding=utf-8
"""
Tenant-aware management command that inspects the additional_data JSON field
on every BiologicalCollectionRecord and, where the institution_id field does
not match the stored 'Collector/Owner Institute' value, updates institution_id
to the value from additional_data.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.fields.json import KeyTextTransform
from django.db.models import F
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger(__name__)

ADDITIONAL_DATA_KEY = 'Collector/Owner Institute'


class Command(BaseCommand):
    help = (
        "For each tenant: update BiologicalCollectionRecord.institution_id from "
        "additional_data['Collector/Owner Institute'] where the two values differ."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-s", "--schema-name",
            dest="schema_names",
            action="append",
            help="Limit to specific tenant schema(s). Can be passed multiple times.",
        )
        parser.add_argument(
            "--all-tenants",
            action="store_true",
            help="Process all tenants (default when no --schema-name is given).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing to the database.",
        )

    def handle(self, *args, **options):
        schema_names = options.get("schema_names") or []
        all_tenants = options.get("all_tenants", False)
        dry_run = options.get("dry_run", False)

        if schema_names and all_tenants:
            raise CommandError("Use either --schema-name or --all-tenants, not both.")

        tenants = self._get_tenants(schema_names)
        if not tenants:
            self.stdout.write(self.style.WARNING("No tenants found."))
            return

        mode = "DRY RUN" if dry_run else "LIVE"
        self.stdout.write(f"{mode}: processing {len(tenants)} tenant(s).")

        for tenant in tenants:
            self.stdout.write(
                f"\n── Tenant: {tenant.name} (schema: {tenant.schema_name})"
            )
            with tenant_context(tenant):
                if dry_run:
                    self._process_tenant(dry_run=True)
                else:
                    with transaction.atomic():
                        self._process_tenant(dry_run=False)

        self.stdout.write(self.style.SUCCESS("\nDone."))

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

        qs = (
            BiologicalCollectionRecord.objects
            .filter(additional_data__has_key=ADDITIONAL_DATA_KEY)
            .exclude(additional_data__contains={ADDITIONAL_DATA_KEY: ''})
            .exclude(additional_data__contains={ADDITIONAL_DATA_KEY: None})
            .annotate(
                ad_institution=KeyTextTransform(ADDITIONAL_DATA_KEY, 'additional_data')
            )
            .exclude(institution_id=F('ad_institution'))
        )

        total = qs.count()
        self.stdout.write(f"  Records to fix: {total}")

        if total == 0:
            return

        if dry_run:
            for rec in qs.iterator(chunk_size=500):
                self.stdout.write(
                    f"  [DRY RUN] pk={rec.pk}: "
                    f"{repr(rec.institution_id)} -> {repr(rec.ad_institution)}"
                )
            return

        updated = 0
        for rec in qs.iterator(chunk_size=500):
            new_value = (rec.ad_institution or "").strip()
            if new_value:
                BiologicalCollectionRecord.objects.filter(pk=rec.pk).update(
                    institution_id=new_value
                )
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"  Updated institution_id on {updated} record(s).")
        )
