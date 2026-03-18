# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Management command to backfill site visits for biological records.

Links records that don't have a survey to an existing or new survey
for their site.

Made with love by Kartoza | https://kartoza.com
"""
import random
import sys
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    """Management command to backfill site visits for records without surveys."""

    help = "Link biological records to site visits (surveys)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="Batch size for updates (default: 5000)",
        )
        parser.add_argument(
            "--stress-test-only",
            action="store_true",
            help="Only process stress test records",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            default=None,
            help="Tenant schema name to process",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        batch_size = options["batch_size"]
        stress_test_only = options["stress_test_only"]
        dry_run = options["dry_run"]
        tenant_name = options["tenant"]

        from django_tenants.utils import tenant_context, get_tenant_model

        Tenant = get_tenant_model()

        if tenant_name:
            try:
                tenant = Tenant.objects.get(schema_name=tenant_name)
            except Tenant.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f"Tenant '{tenant_name}' not found.")
                )
                return
        else:
            tenant = Tenant.objects.exclude(schema_name="public").first()
            if not tenant:
                self.stderr.write(
                    self.style.ERROR("No tenant found. Create a tenant first.")
                )
                return

        self.stdout.write(f"Using tenant: {tenant.name} ({tenant.schema_name})")

        with tenant_context(tenant):
            self._do_backfill(batch_size, stress_test_only, dry_run)

    def _do_backfill(self, batch_size, stress_test_only, dry_run):
        """Perform the backfill within tenant context."""
        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.models.survey import Survey

        User = get_user_model()

        # Get or create a default user for surveys
        default_user, _ = User.objects.get_or_create(
            username="stress_test_user",
            defaults={
                "email": "stress_test@example.com",
                "first_name": "Stress",
                "last_name": "Test",
                "is_active": True,
            },
        )

        # Find records without surveys
        records_qs = BiologicalCollectionRecord.objects.filter(survey__isnull=True)

        if stress_test_only:
            records_qs = records_qs.filter(notes__contains="[STRESS_TEST]")

        total_records = records_qs.count()

        if total_records == 0:
            self.stdout.write(
                self.style.SUCCESS("All records already have site visits linked.")
            )
            return

        self.stdout.write(f"\nFound {total_records:,} records without site visits")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be made"))
            return

        # Build survey cache by site_id
        self.stdout.write("Building survey index...")
        survey_ids_by_site = {}

        if stress_test_only:
            surveys_qs = Survey.objects.filter(
                collector_string__contains="[STRESS_TEST]"
            ).values_list("id", "site_id")
        else:
            surveys_qs = Survey.objects.all().values_list("id", "site_id")

        for survey_id, site_id in surveys_qs.iterator(chunk_size=50000):
            if site_id not in survey_ids_by_site:
                survey_ids_by_site[site_id] = []
            survey_ids_by_site[site_id].append(survey_id)

        self.stdout.write(f"  Indexed {len(survey_ids_by_site):,} sites with surveys")

        # Process records in batches
        self.stdout.write("\nLinking records to site visits...")
        updated = 0
        created_surveys = 0
        processed = 0

        # Get records with their site_id and collection_date
        records_to_update = []

        for record in records_qs.select_related("site").iterator(chunk_size=batch_size):
            site_id = record.site_id

            if not site_id:
                processed += 1
                continue

            # Get or create survey for this site
            survey_ids = survey_ids_by_site.get(site_id)

            if survey_ids:
                # Use existing survey
                survey_id = random.choice(survey_ids)
            else:
                # Create new survey for this site
                survey = Survey.objects.create(
                    site_id=site_id,
                    date=record.collection_date or record.created.date(),
                    collector_string=f"{record.collector or 'Unknown'} [BACKFILL]",
                    owner=record.owner or default_user,
                    collector_user=record.collector_user or default_user,
                    validated=record.validated,
                )
                survey_id = survey.id
                survey_ids_by_site[site_id] = [survey_id]
                created_surveys += 1

            record.survey_id = survey_id
            records_to_update.append(record)
            processed += 1

            # Bulk update when batch is full
            if len(records_to_update) >= batch_size:
                BiologicalCollectionRecord.objects.bulk_update(
                    records_to_update, ["survey_id"]
                )
                updated += len(records_to_update)
                records_to_update = []

                progress = processed / total_records * 100
                self.stdout.write(
                    f"  Progress: {processed:,}/{total_records:,} ({progress:.1f}%) "
                    f"- Updated: {updated:,}, New surveys: {created_surveys:,}",
                    ending="\r",
                )
                sys.stdout.flush()

        # Update remaining records
        if records_to_update:
            BiologicalCollectionRecord.objects.bulk_update(
                records_to_update, ["survey_id"]
            )
            updated += len(records_to_update)

        self.stdout.write(
            f"\n\n"
            f"{'='*60}\n"
            f"Backfill complete!\n"
            f"{'='*60}\n"
            f"Records updated: {updated:,}\n"
            f"New surveys created: {created_surveys:,}\n"
            f"{'='*60}"
        )
