# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Management command to bulk validate pending data.

Validates sites, site visits (surveys), records, and/or taxa proposals.

Made with love by Kartoza | https://kartoza.com
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    """Bulk validate pending biodiversity data."""

    help = "Validate all pending sites, site visits, records, and/or taxa"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sites",
            action="store_true",
            help="Validate all pending location sites",
        )
        parser.add_argument(
            "--site-visits",
            "--surveys",
            action="store_true",
            dest="site_visits",
            help="Validate all pending site visits (surveys)",
        )
        parser.add_argument(
            "--records",
            action="store_true",
            help="Validate all pending biological collection records",
        )
        parser.add_argument(
            "--taxa",
            action="store_true",
            help="Validate all pending taxa",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            dest="validate_all",
            help="Validate all pending items in all categories",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be validated without making changes",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            default=None,
            help="Tenant schema name (default: first non-public tenant)",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        validate_sites = options["sites"] or options["validate_all"]
        validate_site_visits = options["site_visits"] or options["validate_all"]
        validate_records = options["records"] or options["validate_all"]
        validate_taxa = options["taxa"] or options["validate_all"]
        dry_run = options["dry_run"]
        tenant_name = options["tenant"]

        # Check if any option was specified
        if not any([validate_sites, validate_site_visits, validate_records, validate_taxa]):
            self.stderr.write(
                self.style.ERROR(
                    "No category specified. Use --sites, --site-visits, --records, --taxa, or --all"
                )
            )
            return

        # Get tenant
        from django_tenants.utils import tenant_context, get_tenant_model

        Tenant = get_tenant_model()

        if tenant_name:
            try:
                tenant = Tenant.objects.get(schema_name=tenant_name)
            except Tenant.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f"Tenant '{tenant_name}' not found. Available tenants:")
                )
                for t in Tenant.objects.all():
                    self.stderr.write(f"  - {t.schema_name} ({t.name})")
                return
        else:
            tenant = Tenant.objects.exclude(schema_name="public").first()
            if not tenant:
                self.stderr.write(self.style.ERROR("No tenant found."))
                return

        self.stdout.write(f"Using tenant: {tenant.name} ({tenant.schema_name})")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No changes will be made\n"))

        # Execute within tenant context
        with tenant_context(tenant):
            self._do_validate(
                validate_sites,
                validate_site_visits,
                validate_records,
                validate_taxa,
                dry_run,
            )

    def _do_validate(
        self,
        validate_sites,
        validate_site_visits,
        validate_records,
        validate_taxa,
        dry_run,
    ):
        """Perform validation within tenant context."""
        self.stdout.write(
            self.style.NOTICE(
                f"\n{'='*60}\n"
                f"BIMS Bulk Validation\n"
                f"{'='*60}\n"
            )
        )

        total_validated = 0

        with transaction.atomic():
            # Validate sites
            if validate_sites:
                count = self._validate_sites(dry_run)
                total_validated += count

            # Validate site visits (surveys)
            if validate_site_visits:
                count = self._validate_site_visits(dry_run)
                total_validated += count

            # Validate records
            if validate_records:
                count = self._validate_records(dry_run)
                total_validated += count

            # Validate taxa
            if validate_taxa:
                count = self._validate_taxa(dry_run)
                total_validated += count

            if dry_run:
                # Rollback in dry run
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*60}\n"
                f"{'[DRY RUN] Would validate' if dry_run else 'Validated'} {total_validated} total items\n"
                f"{'='*60}\n"
            )
        )

    def _validate_sites(self, dry_run):
        """Validate all pending location sites."""
        from bims.models.location_site import LocationSite

        pending = LocationSite.objects.filter(validated=False, rejected=False)
        count = pending.count()

        if count == 0:
            self.stdout.write("  Sites: No pending sites to validate")
            return 0

        if not dry_run:
            pending.update(validated=True)

        self.stdout.write(
            self.style.SUCCESS(f"  Sites: {'Would validate' if dry_run else 'Validated'} {count} sites")
        )
        return count

    def _validate_site_visits(self, dry_run):
        """Validate all pending site visits (surveys)."""
        from bims.models.survey import Survey
        from bims.models.biological_collection_record import BiologicalCollectionRecord

        pending = Survey.objects.filter(validated=False, rejected=False)
        count = pending.count()

        if count == 0:
            self.stdout.write("  Site Visits: No pending site visits to validate")
            return 0

        if not dry_run:
            # Get survey IDs before updating
            survey_ids = list(pending.values_list("id", flat=True))

            # Validate surveys
            pending.update(validated=True)

            # Also validate all records in these surveys
            records_updated = BiologicalCollectionRecord.objects.filter(
                survey_id__in=survey_ids, validated=False
            ).update(validated=True)

            self.stdout.write(
                self.style.SUCCESS(
                    f"  Site Visits: Validated {count} site visits "
                    f"(+ {records_updated} associated records)"
                )
            )
        else:
            # Count associated records for dry run
            survey_ids = list(pending.values_list("id", flat=True))
            records_count = BiologicalCollectionRecord.objects.filter(
                survey_id__in=survey_ids, validated=False
            ).count()

            self.stdout.write(
                self.style.SUCCESS(
                    f"  Site Visits: Would validate {count} site visits "
                    f"(+ {records_count} associated records)"
                )
            )

        return count

    def _validate_records(self, dry_run):
        """Validate all pending biological collection records."""
        from bims.models.biological_collection_record import BiologicalCollectionRecord

        pending = BiologicalCollectionRecord.objects.filter(validated=False, rejected=False)
        count = pending.count()

        if count == 0:
            self.stdout.write("  Records: No pending records to validate")
            return 0

        if not dry_run:
            pending.update(validated=True)

        self.stdout.write(
            self.style.SUCCESS(f"  Records: {'Would validate' if dry_run else 'Validated'} {count} records")
        )
        return count

    def _validate_taxa(self, dry_run):
        """Validate all pending taxa."""
        from bims.models.taxonomy import Taxonomy

        # Validate unvalidated taxa
        pending = Taxonomy.objects.filter(validated=False, rejected=False)
        count = pending.count()

        if count == 0:
            self.stdout.write("  Taxa: No pending taxa to validate")
            return 0

        if not dry_run:
            pending.update(validated=True)

        self.stdout.write(
            self.style.SUCCESS(f"  Taxa: {'Would validate' if dry_run else 'Validated'} {count} taxa")
        )
        return count
