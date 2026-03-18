# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Management command to load dummy occurrences for BIMS development and testing.

Generates biological collection records for existing sites.

Made with love by Kartoza | https://kartoza.com
"""
import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


# Sample collectors for variety
COLLECTORS = [
    "Dr. Jane van der Berg",
    "Prof. Simon Mkhize",
    "Sarah Williams",
    "John Mokwena",
    "Dr. Themba Ndlovu",
    "Maria van Rooyen",
    "Peter Coetzee",
    "Nomsa Dlamini",
    "Dr. Emily Chen",
    "Robert Smit",
]

# Sampling methods
SAMPLING_METHODS = [
    "kick sampling",
    "sweep netting",
    "electrofishing",
    "seine netting",
    "hand collection",
    "drift netting",
    "baited traps",
    "visual observation",
]

# Habitat types
HABITAT_CHOICES = ["freshwater", "euryhaline"]

# Category choices
CATEGORY_CHOICES = ["indigenous", "alien"]


class Command(BaseCommand):
    """Management command to load dummy occurrence data."""

    help = "Load dummy occurrences for existing BIMS sites"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=1000,
            help="Total number of occurrences to create (default: 1000)",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            default=None,
            help="Tenant schema name to load data into (default: first tenant found)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing dummy occurrences before loading",
        )
        parser.add_argument(
            "--site-id",
            type=int,
            default=None,
            help="Only add occurrences to a specific site ID",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        count = options["count"]
        tenant_name = options["tenant"]
        clear = options["clear"]
        site_id = options["site_id"]

        # Get tenant to use
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
            tenant = Tenant.objects.exclude(schema_name='public').first()
            if not tenant:
                self.stderr.write(
                    self.style.ERROR("No tenant found. Create a tenant first.")
                )
                return

        self.stdout.write(f"Using tenant: {tenant.name} ({tenant.schema_name})")

        with tenant_context(tenant):
            self._do_load(count, clear, site_id)

    def _do_load(self, count, clear, site_id):
        """Perform the actual data loading within a tenant context."""
        from bims.models.location_site import LocationSite
        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.models.taxonomy import Taxonomy
        from bims.models.taxon_group import TaxonGroup
        from bims.models.survey import Survey
        from bims.models.source_reference import SourceReference

        self.stdout.write(
            self.style.NOTICE(
                f"\n{'='*60}\n"
                f"BIMS Dummy Occurrences Loader\n"
                f"{'='*60}\n"
                f"Occurrences to create: {count}\n"
                f"{'='*60}\n"
            )
        )

        try:
            with transaction.atomic():
                if clear:
                    self._clear_dummy_occurrences()

                # Get required data
                user = self._get_or_create_user()

                # Get sites
                if site_id:
                    sites = list(LocationSite.objects.filter(id=site_id))
                    if not sites:
                        self.stderr.write(
                            self.style.ERROR(f"Site with ID {site_id} not found")
                        )
                        return
                else:
                    sites = list(LocationSite.objects.all()[:500])  # Cap at 500 sites

                if not sites:
                    self.stderr.write(
                        self.style.ERROR("No sites found. Run load_dummy_data first.")
                    )
                    return

                self.stdout.write(f"Using {len(sites)} sites")

                # Get taxa
                taxa = list(Taxonomy.objects.all()[:100])  # Cap at 100 taxa
                if not taxa:
                    self.stderr.write(
                        self.style.ERROR("No taxa found. Run load_dummy_data first.")
                    )
                    return

                self.stdout.write(f"Using {len(taxa)} taxa")

                # Get taxon groups
                taxon_groups = {tg.name: tg for tg in TaxonGroup.objects.all()}

                # Get source references
                source_refs = list(SourceReference.objects.all()[:10])

                # Create occurrences
                self._create_occurrences(
                    count, sites, taxa, taxon_groups, user, source_refs
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n{'='*60}\n"
                        f"Dummy occurrences loaded successfully!\n"
                        f"{'='*60}\n"
                    )
                )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error loading dummy data: {e}"))
            import traceback
            traceback.print_exc()

    def _clear_dummy_occurrences(self):
        """Clear existing dummy occurrences."""
        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.models.survey import Survey

        self.stdout.write("Clearing existing dummy occurrences...")

        deleted_records = BiologicalCollectionRecord.objects.filter(
            notes__contains="[DUMMY_DATA]"
        ).delete()
        self.stdout.write(f"  Deleted {deleted_records[0]} biological records")

        deleted_surveys = Survey.objects.filter(
            collector_string__contains="[DUMMY]"
        ).delete()
        self.stdout.write(f"  Deleted {deleted_surveys[0]} surveys")

    def _get_or_create_user(self):
        """Get or create the dummy data user."""
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="dummy_data_user",
            defaults={
                "email": "dummy@example.com",
                "first_name": "Dummy",
                "last_name": "User",
            },
        )
        if created:
            self.stdout.write(f"  Created user: {user.username}")
        return user

    def _create_occurrences(self, count, sites, taxa, taxon_groups, user, source_refs):
        """Create biological collection records."""
        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.models.survey import Survey

        self.stdout.write(f"\nCreating {count} biological records...")

        today = date.today()
        created_count = 0
        batch_size = 100

        # Pre-create some surveys for efficiency
        surveys_per_site = {}

        for i in range(count):
            site = random.choice(sites)

            # Get or create survey for this site
            if site.id not in surveys_per_site:
                surveys_per_site[site.id] = []

            # Create new survey occasionally or reuse existing
            if len(surveys_per_site[site.id]) < 3 or random.random() < 0.1:
                survey_date = today - timedelta(days=random.randint(0, 365 * 5))
                collector = random.choice(COLLECTORS)

                survey = Survey.objects.create(
                    site=site,
                    date=survey_date,
                    collector_string=f"{collector} [DUMMY]",
                    owner=user,
                    collector_user=user,
                    validated=random.random() < 0.7,
                )
                surveys_per_site[site.id].append(survey)
            else:
                survey = random.choice(surveys_per_site[site.id])

            taxon = random.choice(taxa)

            # Determine module group based on taxon
            module_group = None
            for group_name, group in taxon_groups.items():
                if taxon.taxonomies and taxon in group.taxonomies.all():
                    module_group = group
                    break
            if not module_group and taxon_groups:
                module_group = random.choice(list(taxon_groups.values()))

            # Create varied abundance data
            abundance_number = None
            abundance_type = "number"
            if random.random() < 0.8:
                abundance_number = random.randint(1, 500)
                if random.random() < 0.3:
                    abundance_type = random.choice([
                        "number", "percentage", "density"
                    ])

            # Create the record
            record = BiologicalCollectionRecord.objects.create(
                site=site,
                taxonomy=taxon,
                original_species_name=taxon.canonical_name if taxon.canonical_name else str(taxon),
                collection_date=survey.date,
                survey=survey,
                collector=survey.collector_string,
                owner=user,
                collector_user=user,
                module_group=module_group,
                abundance_number=abundance_number,
                abundance_type=abundance_type,
                present=True,
                validated=survey.validated,
                notes=f"[DUMMY_DATA] Test record for {taxon.canonical_name if taxon.canonical_name else taxon}",
                source_reference=random.choice(source_refs) if source_refs and random.random() < 0.7 else None,
                collection_habitat=random.choice(HABITAT_CHOICES) if random.random() < 0.5 else "",
                sampling_effort=f"{random.randint(1, 60)} minutes" if random.random() < 0.4 else "",
            )

            created_count += 1

            if created_count % batch_size == 0:
                self.stdout.write(f"  Created {created_count}/{count} records...")

        self.stdout.write(self.style.SUCCESS(f"  Created {created_count} biological records"))
