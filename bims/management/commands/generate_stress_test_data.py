# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Management command to generate large-scale stress test data for BIMS.

Generates 1 million random sites across Africa and 10 million biological
collection records distributed across fish, invertebrates, and algae taxon groups.
Each record is linked to a site via a site visit (survey).

Optimized for bulk inserts with progress tracking.

Made with love by Kartoza | https://kartoza.com
"""
import logging
import random
import sys
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import connection, transaction

logger = logging.getLogger("bims")

# Africa bounding box (approximate)
AFRICA_BOUNDS = {
    "min_lat": -35.0,
    "max_lat": 37.5,
    "min_lon": -18.0,
    "max_lon": 52.0,
}

# Major regions in Africa for realistic site distribution
AFRICA_REGIONS = [
    # Southern Africa
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241, "radius": 0.8},
    {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473, "radius": 0.6},
    {"name": "Durban", "lat": -29.8587, "lon": 31.0218, "radius": 0.5},
    {"name": "Kruger", "lat": -24.0, "lon": 31.5, "radius": 1.0},
    {"name": "Victoria Falls", "lat": -17.9243, "lon": 25.8572, "radius": 0.5},
    {"name": "Okavango Delta", "lat": -19.2833, "lon": 22.7833, "radius": 1.2},
    {"name": "Drakensberg", "lat": -29.0, "lon": 29.5, "radius": 0.8},
    {"name": "Karoo", "lat": -32.5, "lon": 22.0, "radius": 1.5},
    # East Africa
    {"name": "Lake Victoria", "lat": -1.2921, "lon": 33.0, "radius": 2.0},
    {"name": "Lake Tanganyika", "lat": -6.0, "lon": 29.5, "radius": 1.5},
    {"name": "Lake Malawi", "lat": -12.0, "lon": 34.5, "radius": 1.2},
    {"name": "Nile Delta", "lat": 30.8, "lon": 31.0, "radius": 1.0},
    {"name": "Mount Kenya", "lat": -0.15, "lon": 37.3, "radius": 0.6},
    {"name": "Serengeti", "lat": -2.3333, "lon": 34.8333, "radius": 1.0},
    {"name": "Kilimanjaro", "lat": -3.0674, "lon": 37.3556, "radius": 0.5},
    # West Africa
    {"name": "Niger Delta", "lat": 4.75, "lon": 6.0, "radius": 1.5},
    {"name": "Lake Chad", "lat": 13.5, "lon": 14.0, "radius": 1.5},
    {"name": "Senegal River", "lat": 16.0, "lon": -16.0, "radius": 1.0},
    {"name": "Congo Basin", "lat": 0.0, "lon": 18.0, "radius": 3.0},
    {"name": "Lake Volta", "lat": 7.5, "lon": -0.5, "radius": 1.0},
    # North Africa
    {"name": "Atlas Mountains", "lat": 31.0, "lon": -5.0, "radius": 1.5},
    {"name": "Nile Valley", "lat": 25.0, "lon": 32.5, "radius": 2.0},
    # Central Africa
    {"name": "Zambezi", "lat": -15.0, "lon": 28.0, "radius": 1.5},
    {"name": "Limpopo", "lat": -23.0, "lon": 30.0, "radius": 1.0},
    {"name": "Orange River", "lat": -29.0, "lon": 19.0, "radius": 1.5},
]

# Ecosystem types
ECOSYSTEM_TYPES = ["river", "wetland", "estuary", "dam", "lake", "stream", "spring"]

# Sample collectors
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
    "Dr. Ahmed Hassan",
    "Prof. Fatima Okonkwo",
    "David Mwangi",
    "Dr. Sophie Leclerc",
    "James Oduya",
]


class Command(BaseCommand):
    """Management command to generate large-scale stress test data."""

    help = "Generate 1 million sites and 10 million records for stress testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sites",
            type=int,
            default=1_000_000,
            help="Number of location sites to create (default: 1,000,000)",
        )
        parser.add_argument(
            "--records",
            type=int,
            default=10_000_000,
            help="Number of biological records to create (default: 10,000,000)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10000,
            help="Batch size for bulk inserts (default: 10000)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing stress test data before loading",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            default=None,
            help="Tenant schema name to load data into",
        )
        parser.add_argument(
            "--skip-sites",
            action="store_true",
            help="Skip site generation (use existing sites)",
        )
        parser.add_argument(
            "--skip-records",
            action="store_true",
            help="Skip record generation",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        num_sites = options["sites"]
        num_records = options["records"]
        batch_size = options["batch_size"]
        clear = options["clear"]
        tenant_name = options["tenant"]
        skip_sites = options["skip_sites"]
        skip_records = options["skip_records"]

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

        # Execute within tenant context
        with tenant_context(tenant):
            self._do_generate(
                num_sites, num_records, batch_size, clear, skip_sites, skip_records
            )

    def _do_generate(
        self, num_sites, num_records, batch_size, clear, skip_sites, skip_records
    ):
        """Perform the actual data generation within a tenant context."""
        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.models.location_site import LocationSite
        from bims.models.location_type import LocationType
        from bims.models.survey import Survey
        from bims.models.taxon_group import TaxonGroup
        from bims.models.taxonomy import Taxonomy

        self.stdout.write(
            self.style.NOTICE(
                f"\n{'='*60}\n"
                f"BIMS Stress Test Data Generator\n"
                f"{'='*60}\n"
                f"Sites to create: {num_sites:,}\n"
                f"Records to create: {num_records:,}\n"
                f"Batch size: {batch_size:,}\n"
                f"{'='*60}\n"
            )
        )

        if clear:
            self._clear_stress_test_data()

        # Get or create required supporting data
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username="stress_test_user",
            defaults={
                "email": "stress_test@example.com",
                "first_name": "Stress",
                "last_name": "Test",
                "is_active": True,
            },
        )

        location_type, _ = LocationType.objects.get_or_create(
            name="PointObservation",
            defaults={
                "description": "Point observation location",
                "allowed_geometry": "POINT",
            },
        )

        # Get or create taxon groups
        taxon_groups = self._ensure_taxon_groups()

        # Get or create taxa
        taxa_by_group = self._ensure_taxa(taxon_groups)

        # Create sites
        site_ids = []
        if not skip_sites:
            site_ids = self._create_sites_bulk(
                num_sites, location_type, user, batch_size
            )
        else:
            # Get existing stress test site IDs
            site_ids = list(
                LocationSite.objects.filter(
                    site_description__contains="[STRESS_TEST]"
                ).values_list("id", flat=True)
            )
            if not site_ids:
                # Use all sites if no stress test sites exist
                site_ids = list(LocationSite.objects.values_list("id", flat=True))
            self.stdout.write(f"Using {len(site_ids):,} existing sites")

        if not site_ids:
            self.stderr.write(self.style.ERROR("No sites available for records"))
            return

        # Create records with site visits
        if not skip_records:
            self._create_records_bulk(
                num_records, site_ids, taxa_by_group, taxon_groups, user, batch_size
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*60}\n"
                f"Stress test data generation complete!\n"
                f"{'='*60}\n"
            )
        )

    def _clear_stress_test_data(self):
        """Clear existing stress test data using raw SQL for speed."""
        self.stdout.write("Clearing existing stress test data...")

        with connection.cursor() as cursor:
            # Delete records
            cursor.execute(
                "DELETE FROM bims_biologicalcollectionrecord WHERE notes LIKE '%[STRESS_TEST]%'"
            )
            self.stdout.write(f"  Deleted {cursor.rowcount:,} biological records")

            # Delete surveys
            cursor.execute(
                "DELETE FROM bims_survey WHERE collector_string LIKE '%[STRESS_TEST]%'"
            )
            self.stdout.write(f"  Deleted {cursor.rowcount:,} surveys")

            # Delete sites
            cursor.execute(
                "DELETE FROM bims_locationsite WHERE site_description LIKE '%[STRESS_TEST]%'"
            )
            self.stdout.write(f"  Deleted {cursor.rowcount:,} location sites")

    def _ensure_taxon_groups(self):
        """Ensure taxon groups exist."""
        from bims.models.taxon_group import TaxonGroup

        groups = {}
        group_configs = [
            {"name": "Fish", "singular_name": "Fish", "category": "SPECIES_MODULE"},
            {"name": "Invertebrates", "singular_name": "Invertebrate", "category": "SPECIES_MODULE"},
            {"name": "Algae", "singular_name": "Alga", "category": "SPECIES_MODULE"},
        ]

        for config in group_configs:
            group, created = TaxonGroup.objects.get_or_create(
                name=config["name"],
                defaults={
                    "singular_name": config["singular_name"],
                    "category": config["category"],
                },
            )
            groups[config["name"]] = group
            if created:
                self.stdout.write(f"  Created taxon group: {group.name}")

        return groups

    def _ensure_taxa(self, taxon_groups):
        """Create taxa for each group if they don't exist."""
        from bims.models.taxonomy import Taxonomy

        # Sample taxa for each group
        fish_taxa = [
            "Labeobarbus aeneus", "Labeobarbus kimberleyensis", "Clarias gariepinus",
            "Tilapia sparrmanii", "Pseudocrenilabrus philander", "Barbus anoplus",
            "Labeo umbratus", "Oreochromis mossambicus", "Amphilius uranoscopus",
            "Enteromius paludinosus", "Enteromius trimaculatus", "Labeo capensis",
            "Austroglanis sclateri", "Barbus pallidus", "Labeobarbus capensis",
        ]

        invertebrate_taxa = [
            "Baetidae sp.", "Heptageniidae sp.", "Caenidae sp.", "Hydropsychidae sp.",
            "Simuliidae sp.", "Chironomidae sp.", "Aeshnidae sp.", "Libellulidae sp.",
            "Coenagrionidae sp.", "Potamonautidae sp.", "Corbiculidae sp.", "Gomphidae sp.",
            "Leptophlebiidae sp.", "Tricorythidae sp.", "Perlidae sp.",
        ]

        algae_taxa = [
            "Cladophora sp.", "Spirogyra sp.", "Oedogonium sp.", "Zygnema sp.",
            "Mougeotia sp.", "Vaucheria sp.", "Chara sp.", "Nitella sp.",
            "Navicula sp.", "Pinnularia sp.", "Oscillatoria sp.", "Anabaena sp.",
            "Microcystis sp.", "Scenedesmus sp.", "Pediastrum sp.",
        ]

        taxa_by_group = {"Fish": [], "Invertebrates": [], "Algae": []}

        # Create fish taxa
        fish_group = taxon_groups.get("Fish")
        for name in fish_taxa:
            taxonomy, created = Taxonomy.objects.get_or_create(
                canonical_name=name,
                defaults={
                    "scientific_name": name,
                    "rank": "SPECIES",
                    "taxonomic_status": "ACCEPTED",
                    "verified": True,
                },
            )
            if fish_group and taxonomy not in fish_group.taxonomies.all():
                fish_group.taxonomies.add(taxonomy)
            taxa_by_group["Fish"].append(taxonomy.id)

        # Create invertebrate taxa
        invert_group = taxon_groups.get("Invertebrates")
        for name in invertebrate_taxa:
            taxonomy, created = Taxonomy.objects.get_or_create(
                canonical_name=name,
                defaults={
                    "scientific_name": name,
                    "rank": "FAMILY",
                    "taxonomic_status": "ACCEPTED",
                    "verified": True,
                },
            )
            if invert_group and taxonomy not in invert_group.taxonomies.all():
                invert_group.taxonomies.add(taxonomy)
            taxa_by_group["Invertebrates"].append(taxonomy.id)

        # Create algae taxa
        algae_group = taxon_groups.get("Algae")
        for name in algae_taxa:
            taxonomy, created = Taxonomy.objects.get_or_create(
                canonical_name=name,
                defaults={
                    "scientific_name": name,
                    "rank": "GENUS",
                    "taxonomic_status": "ACCEPTED",
                    "verified": True,
                },
            )
            if algae_group and taxonomy not in algae_group.taxonomies.all():
                algae_group.taxonomies.add(taxonomy)
            taxa_by_group["Algae"].append(taxonomy.id)

        total_taxa = sum(len(t) for t in taxa_by_group.values())
        self.stdout.write(f"Ensured {total_taxa} taxa across 3 groups")

        return taxa_by_group

    def _create_sites_bulk(self, num_sites, location_type, user, batch_size):
        """Create sites using bulk insert for performance."""
        from bims.models.location_site import LocationSite

        self.stdout.write(f"\nCreating {num_sites:,} location sites...")

        # Track the last ID before we start for querying back
        last_id_before = (
            LocationSite.objects.order_by("-id").values_list("id", flat=True).first()
            or 0
        )

        sites_batch = []
        total_inserted = 0

        for i in range(num_sites):
            # Generate coordinates - 70% near regions, 30% random
            if random.random() < 0.7:
                region = random.choice(AFRICA_REGIONS)
                lat = region["lat"] + random.uniform(-region["radius"], region["radius"])
                lon = region["lon"] + random.uniform(-region["radius"], region["radius"])
            else:
                lat = random.uniform(AFRICA_BOUNDS["min_lat"], AFRICA_BOUNDS["max_lat"])
                lon = random.uniform(AFRICA_BOUNDS["min_lon"], AFRICA_BOUNDS["max_lon"])

            ecosystem = random.choice(ECOSYSTEM_TYPES)
            site_code = f"ST-{i+1:07d}"

            site = LocationSite(
                name=f"Stress Test Site {i+1}",
                site_code=site_code,
                site_description=f"[STRESS_TEST] Auto-generated stress test site",
                geometry_point=Point(lon, lat, srid=4326),
                latitude=lat,
                longitude=lon,
                location_type=location_type,
                ecosystem_type=ecosystem,
                creator=user,
                owner=user,
                validated=True,
            )
            sites_batch.append(site)

            # Bulk insert when batch is full
            if len(sites_batch) >= batch_size:
                # Don't use ignore_conflicts - we want the IDs returned
                LocationSite.objects.bulk_create(sites_batch)
                total_inserted += len(sites_batch)
                sites_batch = []

                progress = (i + 1) / num_sites * 100
                self.stdout.write(
                    f"  Progress: {i + 1:,}/{num_sites:,} ({progress:.1f}%)",
                    ending="\r"
                )
                sys.stdout.flush()

        # Insert remaining sites
        if sites_batch:
            LocationSite.objects.bulk_create(sites_batch)
            total_inserted += len(sites_batch)

        # Query back all the IDs we just created
        site_ids = list(
            LocationSite.objects.filter(
                id__gt=last_id_before,
                site_description__contains="[STRESS_TEST]"
            ).values_list("id", flat=True)
        )

        self.stdout.write(f"\n  Created {len(site_ids):,} location sites")
        return site_ids

    def _create_records_bulk(
        self, num_records, site_ids, taxa_by_group, taxon_groups, user, batch_size
    ):
        """Create biological records with site visits using bulk insert."""
        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.models.survey import Survey

        self.stdout.write(f"\nCreating {num_records:,} biological records...")

        today = date.today()
        records_per_group = num_records // 3
        remainder = num_records % 3

        group_names = ["Fish", "Invertebrates", "Algae"]
        group_record_counts = [records_per_group] * 3
        group_record_counts[0] += remainder  # Give remainder to fish

        # Create a pool of surveys to reuse (each site gets 1-3 surveys)
        self.stdout.write("  Creating site visits (surveys)...")

        # Track last survey ID before we start
        last_survey_id = (
            Survey.objects.order_by("-id").values_list("id", flat=True).first() or 0
        )

        surveys_batch = []
        total_surveys_created = 0

        for idx, site_id in enumerate(site_ids):
            num_surveys = random.randint(1, 3)

            for _ in range(num_surveys):
                survey_date = today - timedelta(days=random.randint(0, 365 * 5))
                collector = random.choice(COLLECTORS)

                survey = Survey(
                    site_id=site_id,
                    date=survey_date,
                    collector_string=f"{collector} [STRESS_TEST]",
                    owner=user,
                    collector_user=user,
                    validated=True,
                )
                surveys_batch.append(survey)

            if len(surveys_batch) >= batch_size:
                Survey.objects.bulk_create(surveys_batch)
                total_surveys_created += len(surveys_batch)
                surveys_batch = []

                if (idx + 1) % 100000 == 0:
                    self.stdout.write(
                        f"    Created surveys for {idx + 1:,}/{len(site_ids):,} sites",
                        ending="\r"
                    )
                    sys.stdout.flush()

        # Insert remaining surveys
        if surveys_batch:
            Survey.objects.bulk_create(surveys_batch)
            total_surveys_created += len(surveys_batch)

        self.stdout.write(f"\n  Created {total_surveys_created:,} site visits")

        # Query back all surveys and build the mapping
        self.stdout.write("  Building survey index...")
        survey_ids_by_site = {}
        surveys_qs = Survey.objects.filter(
            id__gt=last_survey_id,
            collector_string__contains="[STRESS_TEST]"
        ).values_list("id", "site_id")

        for survey_id, site_id in surveys_qs.iterator(chunk_size=50000):
            if site_id not in survey_ids_by_site:
                survey_ids_by_site[site_id] = []
            survey_ids_by_site[site_id].append(survey_id)

        self.stdout.write(f"  Indexed {len(survey_ids_by_site):,} sites with surveys")

        # Now create records
        self.stdout.write("  Creating biological records...")
        records_batch = []
        total_created = 0
        skipped = 0

        for group_idx, group_name in enumerate(group_names):
            target_count = group_record_counts[group_idx]
            taxa_ids = taxa_by_group[group_name]
            taxon_group = taxon_groups[group_name]

            self.stdout.write(f"    Creating {target_count:,} {group_name} records...")

            for i in range(target_count):
                # Pick random site and survey
                site_id = random.choice(site_ids)
                site_survey_ids = survey_ids_by_site.get(site_id)

                if not site_survey_ids:
                    skipped += 1
                    continue

                survey_id = random.choice(site_survey_ids)
                taxonomy_id = random.choice(taxa_ids)
                collector = random.choice(COLLECTORS)

                record = BiologicalCollectionRecord(
                    site_id=site_id,
                    taxonomy_id=taxonomy_id,
                    original_species_name=f"Species {taxonomy_id}",
                    collection_date=today - timedelta(days=random.randint(0, 365 * 5)),
                    survey_id=survey_id,
                    collector=f"{collector} [STRESS_TEST]",
                    owner=user,
                    collector_user=user,
                    module_group=taxon_group,
                    abundance_number=random.randint(1, 100) if random.random() < 0.7 else None,
                    present=True,
                    validated=True,
                    notes="[STRESS_TEST] Auto-generated stress test record",
                )
                records_batch.append(record)

                if len(records_batch) >= batch_size:
                    BiologicalCollectionRecord.objects.bulk_create(records_batch)
                    total_created += len(records_batch)
                    records_batch = []

                    progress = (total_created / num_records) * 100
                    self.stdout.write(
                        f"    Progress: {total_created:,}/{num_records:,} ({progress:.1f}%)",
                        ending="\r"
                    )
                    sys.stdout.flush()

        # Insert remaining records
        if records_batch:
            BiologicalCollectionRecord.objects.bulk_create(records_batch)
            total_created += len(records_batch)

        self.stdout.write(f"\n  Created {total_created:,} biological records")
        if skipped:
            self.stdout.write(f"  (Skipped {skipped:,} records due to missing surveys)")
