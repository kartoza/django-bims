# coding=utf-8
"""
Backfill BiologicalCollectionRecord.created_date / modified_date from the
GBIF harvest timestamp stored in additional_data['date_fetched'].

Records harvested from GBIF store, in their JSON additional_data:

    {
        "fetch_from_gbif": true,
        "date_fetched": "2024-01-01 12:00:00"
    }

The created_date / modified_date columns were added later, so historical
records have them NULL. This command seeds those columns from date_fetched
so the "how old is this data" signal is available on an indexed column
(useful for prioritising which records to re-check against upstream GBIF).

Only rows where modified_date IS NULL are touched, so it is safe to re-run.
created_date is only filled where it is currently NULL (existing values are
preserved).
"""

from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import DataError, transaction
from django.db.models import DateTimeField
from django.db.models.functions import Cast, Coalesce
from django.db.models.fields.json import KeyTextTransform
from django.utils import timezone
from django_tenants.utils import get_tenant_model, tenant_context

from bims.models.biological_collection_record import BiologicalCollectionRecord

DATE_FETCHED_FORMAT = '%Y-%m-%d %H:%M:%S'


class Command(BaseCommand):
    help = (
        "Backfill created_date/modified_date on BiologicalCollectionRecord "
        "from additional_data['date_fetched']."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-s", "--schema-name",
            dest="schema_names",
            action="append",
            help="Limit to specific tenant schema(s). May be repeated.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="Number of rows to update per batch (default: 5000).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report how many rows would be updated; change nothing.",
        )

    def handle(self, *args, **options):
        schema_names = options.get("schema_names") or []
        self.batch_size = options.get("batch_size") or 5000
        self.dry_run = options.get("dry_run", False)

        tenants = get_tenant_model().objects.all()
        if schema_names:
            tenants = tenants.filter(schema_name__in=schema_names)

        grand_total = 0
        for tenant in tenants:
            with tenant_context(tenant):
                self.stdout.write(self.style.MIGRATE_HEADING(
                    "Schema: %s" % tenant.schema_name))
                grand_total += self.backfill_schema()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "Done. %d record(s) %s." % (
                grand_total,
                "would be updated" if self.dry_run else "updated")))

    def base_queryset(self):
        return BiologicalCollectionRecord.objects.filter(
            additional_data__has_key='date_fetched',
            modified_date__isnull=True,
        )

    def backfill_schema(self):
        total = self.base_queryset().count()
        self.stdout.write(
            "  %d record(s) with date_fetched and no modified_date." % total)
        if not total or self.dry_run:
            return total

        fetched = Cast(
            KeyTextTransform('date_fetched', 'additional_data'),
            output_field=DateTimeField(),
        )

        updated = 0
        while True:
            batch_ids = list(
                self.base_queryset().values_list('pk', flat=True)[:self.batch_size]
            )
            if not batch_ids:
                break
            qs = BiologicalCollectionRecord.objects.filter(pk__in=batch_ids)
            try:
                with transaction.atomic():
                    qs.update(
                        modified_date=fetched,
                        created_date=Coalesce('created_date', fetched),
                    )
            except DataError:
                # A malformed date_fetched value broke the SQL cast; fall
                # back to parsing this batch row by row so one bad value
                # does not block the rest.
                self.stderr.write(self.style.WARNING(
                    "  Cast failed for a batch; parsing it in Python..."))
                updated += self.backfill_batch_python(batch_ids)
            else:
                updated += len(batch_ids)
            self.stdout.write("  updated %d/%d..." % (updated, total))

        return updated

    def backfill_batch_python(self, batch_ids):
        records = BiologicalCollectionRecord.objects.filter(pk__in=batch_ids)
        to_update = []
        for record in records:
            raw = (record.additional_data or {}).get('date_fetched')
            parsed = self.parse_date(raw)
            if parsed is None:
                continue
            record.modified_date = parsed
            if record.created_date is None:
                record.created_date = parsed
            to_update.append(record)
        if to_update:
            BiologicalCollectionRecord.objects.bulk_update(
                to_update, ['modified_date', 'created_date'])
        return len(to_update)

    @staticmethod
    def parse_date(raw):
        if not raw:
            return None
        try:
            parsed = datetime.strptime(str(raw).strip(), DATE_FETCHED_FORMAT)
        except (ValueError, TypeError):
            return None
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(
                parsed, timezone.get_current_timezone())
        return parsed
