# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Management command to load dummy data for BIMS development and testing.

Generates location sites across South Africa and populates them with
taxa fetched from GBIF and biological collection records.

Made with love by Kartoza | https://kartoza.com
"""
import logging
import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger("bims")

# South Africa bounding box (approximate)
SA_BOUNDS = {
    "min_lat": -35.0,
    "max_lat": -22.0,
    "min_lon": 16.0,
    "max_lon": 33.0,
}

# Major cities/regions in South Africa for realistic site distribution
SA_REGIONS = [
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241, "radius": 0.5},
    {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473, "radius": 0.4},
    {"name": "Durban", "lat": -29.8587, "lon": 31.0218, "radius": 0.4},
    {"name": "Pretoria", "lat": -25.7479, "lon": 28.2293, "radius": 0.3},
    {"name": "Port Elizabeth", "lat": -33.9608, "lon": 25.6022, "radius": 0.3},
    {"name": "Bloemfontein", "lat": -29.0852, "lon": 26.1596, "radius": 0.3},
    {"name": "East London", "lat": -33.0153, "lon": 27.9116, "radius": 0.3},
    {"name": "Kimberley", "lat": -28.7323, "lon": 24.7623, "radius": 0.3},
    {"name": "Polokwane", "lat": -23.9045, "lon": 29.4688, "radius": 0.3},
    {"name": "Nelspruit", "lat": -25.4753, "lon": 30.9694, "radius": 0.3},
    {"name": "Kruger National Park", "lat": -24.0, "lon": 31.5, "radius": 0.8},
    {"name": "Drakensberg", "lat": -29.0, "lon": 29.5, "radius": 0.6},
    {"name": "Garden Route", "lat": -33.9, "lon": 22.5, "radius": 0.4},
    {"name": "Wild Coast", "lat": -32.0, "lon": 29.0, "radius": 0.4},
    {"name": "Karoo", "lat": -32.5, "lon": 22.0, "radius": 1.0},
]

# Ecosystem types
ECOSYSTEM_TYPES = ["river", "wetland", "estuary", "dam", "lake"]

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

# South African freshwater fish species to search on GBIF
SA_FISH_SPECIES = [
    "Labeobarbus aeneus",  # Smallmouth yellowfish
    "Labeobarbus kimberleyensis",  # Largemouth yellowfish
    "Labeobarbus capensis",  # Clanwilliam yellowfish
    "Clarias gariepinus",  # African sharptooth catfish
    "Tilapia sparrmanii",  # Banded tilapia
    "Pseudocrenilabrus philander",  # Southern mouthbrooder
    "Barbus anoplus",  # Chubbyhead barb
    "Barbus pallidus",  # Goldie barb
    "Enteromius paludinosus",  # Straightfin barb
    "Enteromius trimaculatus",  # Threespot barb
    "Labeo umbratus",  # Moggel
    "Labeo capensis",  # Orange River mudfish
    "Austroglanis sclateri",  # Rock catfish
    "Amphilius uranoscopus",  # Stargazer catfish
    "Oreochromis mossambicus",  # Mozambique tilapia
]

# South African aquatic invertebrate families for GBIF
SA_INVERTEBRATE_FAMILIES = [
    "Baetidae",  # Small minnow mayflies
    "Heptageniidae",  # Flatheaded mayflies
    "Caenidae",  # Small squaregill mayflies
    "Hydropsychidae",  # Net-spinning caddisflies
    "Simuliidae",  # Blackflies
    "Chironomidae",  # Midges
    "Aeshnidae",  # Hawker dragonflies
    "Libellulidae",  # Skimmer dragonflies
    "Coenagrionidae",  # Narrow-winged damselflies
    "Potamonautidae",  # Freshwater crabs
]

# Algae genera
SA_ALGAE_GENERA = [
    "Cladophora",
    "Spirogyra",
    "Oedogonium",
    "Zygnema",
    "Mougeotia",
    "Vaucheria",
    "Chara",
    "Nitella",
    "Navicula",
    "Pinnularia",
]


class Command(BaseCommand):
    """Management command to load dummy biodiversity data."""

    help = "Load dummy data for BIMS development (sites, taxa from GBIF, records)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sites",
            type=int,
            default=50,
            help="Number of location sites to create (default: 50)",
        )
        parser.add_argument(
            "--site-visits",
            type=int,
            default=0,
            help="Number of site visits (surveys) to create (default: auto based on sites)",
        )
        parser.add_argument(
            "--records-per-site",
            type=int,
            default=10,
            help="Average records per site (default: 10)",
        )
        parser.add_argument(
            "--skip-gbif",
            action="store_true",
            help="Skip GBIF lookups (use local taxa only)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing dummy data before loading",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            default=None,
            help="Tenant schema name to load data into (default: first tenant found)",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        num_sites = options["sites"]
        num_site_visits = options["site_visits"]
        records_per_site = options["records_per_site"]
        skip_gbif = options["skip_gbif"]
        clear = options["clear"]
        tenant_name = options["tenant"]

        # Get tenant to use
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
            # Use first non-public tenant
            tenant = Tenant.objects.exclude(schema_name='public').first()
            if not tenant:
                self.stderr.write(
                    self.style.ERROR("No tenant found. Create a tenant first.")
                )
                return

        self.stdout.write(f"Using tenant: {tenant.name} ({tenant.schema_name})")

        # Execute within tenant context
        with tenant_context(tenant):
            self._do_load(num_sites, num_site_visits, records_per_site, skip_gbif, clear)

    def _do_load(self, num_sites, num_site_visits, records_per_site, skip_gbif, clear):
        """Perform the actual data loading within a tenant context."""

        self.stdout.write(
            self.style.NOTICE(
                f"\n{'='*60}\n"
                f"BIMS Dummy Data Loader\n"
                f"{'='*60}\n"
                f"Sites to create: {num_sites}\n"
                f"Site visits to create: {num_site_visits if num_site_visits > 0 else 'auto'}\n"
                f"Records per site: ~{records_per_site}\n"
                f"GBIF lookups: {'disabled' if skip_gbif else 'enabled'}\n"
                f"{'='*60}\n"
            )
        )

        try:
            with transaction.atomic():
                if clear:
                    self._clear_dummy_data()

                # Create or get required supporting data
                user = self._get_or_create_user()
                location_type = self._get_or_create_location_type()
                taxon_groups = self._get_or_create_taxon_groups()

                # Fetch or create taxa
                taxa = self._get_or_create_taxa(taxon_groups, skip_gbif)

                # Create sites
                sites = self._create_sites(num_sites, location_type, user)

                # Create source references
                source_refs = self._create_source_references(user)

                # Create boundaries
                self._create_boundaries(user)

                # Create site visits (surveys)
                surveys = []
                if num_site_visits > 0:
                    surveys = self._create_site_visits(sites, user, num_site_visits)

                # Create biological records
                self._create_records(sites, taxa, taxon_groups, user, records_per_site, source_refs, surveys)

                # Count totals
                from bims.models.survey import Survey
                total_surveys = Survey.objects.filter(collector_string__contains="[DUMMY]").count()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n{'='*60}\n"
                        f"Dummy data loaded successfully!\n"
                        f"{'='*60}\n"
                        f"Created {len(sites)} location sites\n"
                        f"Created {len(taxa)} taxa\n"
                        f"Created {total_surveys} site visits (surveys)\n"
                        f"{'='*60}\n"
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading dummy data: {e}"))
            raise

    def _clear_dummy_data(self):
        """Clear existing dummy data."""
        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.models.location_site import LocationSite
        from bims.models.survey import Survey

        self.stdout.write("Clearing existing dummy data...")

        # Delete records with dummy marker
        deleted_records = BiologicalCollectionRecord.objects.filter(
            notes__contains="[DUMMY_DATA]"
        ).delete()
        self.stdout.write(f"  Deleted {deleted_records[0]} biological records")

        # Delete surveys with dummy marker
        deleted_surveys = Survey.objects.filter(
            collector_string__contains="[DUMMY]"
        ).delete()
        self.stdout.write(f"  Deleted {deleted_surveys[0]} surveys")

        # Delete sites with dummy marker
        deleted_sites = LocationSite.objects.filter(
            site_description__contains="[DUMMY_DATA]"
        ).delete()
        self.stdout.write(f"  Deleted {deleted_sites[0]} location sites")

    def _get_or_create_user(self):
        """Get or create a user for dummy data."""
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="dummy_data_user",
            defaults={
                "email": "dummy@example.com",
                "first_name": "Dummy",
                "last_name": "User",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"  Created user: {user.username}")
        return user

    def _get_or_create_location_type(self):
        """Get or create location type for sites."""
        from bims.models.location_type import LocationType

        location_type, created = LocationType.objects.get_or_create(
            name="PointObservation",
            defaults={
                "description": "Point observation location",
                "allowed_geometry": "POINT",
            },
        )
        if created:
            self.stdout.write(f"  Created location type: {location_type.name}")
        return location_type

    def _get_or_create_taxon_groups(self):
        """Get or create taxon groups."""
        from bims.models.taxon_group import TaxonGroup

        groups = {}
        group_configs = [
            {"name": "Fish", "singular_name": "Fish", "category": "SPECIES_MODULE"},
            {
                "name": "Invertebrates",
                "singular_name": "Invertebrate",
                "category": "SPECIES_MODULE",
            },
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

    def _get_or_create_taxa(self, taxon_groups, skip_gbif=False):
        """Fetch taxa from GBIF or create locally."""
        from bims.models.taxonomy import Taxonomy

        taxa = []

        if not skip_gbif:
            self.stdout.write("\nFetching taxa from GBIF...")
            taxa.extend(self._fetch_gbif_taxa(SA_FISH_SPECIES, "Fish", taxon_groups))
            taxa.extend(
                self._fetch_gbif_taxa(
                    SA_INVERTEBRATE_FAMILIES, "Invertebrates", taxon_groups, rank="FAMILY"
                )
            )
            taxa.extend(
                self._fetch_gbif_taxa(
                    SA_ALGAE_GENERA, "Algae", taxon_groups, rank="GENUS"
                )
            )

        # If no taxa from GBIF or skip_gbif, create local taxa
        if not taxa:
            self.stdout.write("Creating local taxa (GBIF disabled or unavailable)...")
            taxa = self._create_local_taxa(taxon_groups)

        return taxa

    def _fetch_gbif_taxa(self, species_list, group_name, taxon_groups, rank="SPECIES"):
        """Fetch taxa from GBIF API."""
        taxa = []

        try:
            from pygbif import species as gbif_species
        except ImportError:
            self.stdout.write(
                self.style.WARNING("  pygbif not available, skipping GBIF lookups")
            )
            return taxa

        from bims.models.taxonomy import Taxonomy

        group = taxon_groups.get(group_name)

        for name in species_list:
            try:
                # Search GBIF for the species
                result = gbif_species.name_backbone(name=name, rank=rank, strict=False)

                if result.get("matchType") == "NONE":
                    self.stdout.write(f"    No GBIF match for: {name}")
                    continue

                gbif_key = result.get("usageKey")
                canonical_name = result.get("canonicalName", name)
                scientific_name = result.get("scientificName", name)
                taxon_rank = result.get("rank", rank)

                # Get or create taxonomy
                taxonomy, created = Taxonomy.objects.get_or_create(
                    gbif_key=gbif_key,
                    defaults={
                        "scientific_name": scientific_name,
                        "canonical_name": canonical_name,
                        "rank": taxon_rank,
                        "taxonomic_status": result.get("status", "ACCEPTED"),
                        "gbif_data": result,
                        "verified": True,
                    },
                )

                if created:
                    self.stdout.write(f"    Created: {canonical_name} (GBIF: {gbif_key})")
                else:
                    self.stdout.write(f"    Exists: {canonical_name}")

                # Add to taxon group
                if group and taxonomy not in group.taxonomies.all():
                    group.taxonomies.add(taxonomy)

                taxa.append(taxonomy)

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"    Error fetching {name}: {e}")
                )

        return taxa

    def _create_local_taxa(self, taxon_groups):
        """Create local taxa without GBIF."""
        from bims.models.taxonomy import Taxonomy

        taxa = []

        # Create fish species locally
        fish_group = taxon_groups.get("Fish")
        for name in SA_FISH_SPECIES[:5]:  # Just first 5
            taxonomy, created = Taxonomy.objects.get_or_create(
                canonical_name=name,
                defaults={
                    "scientific_name": name,
                    "rank": "SPECIES",
                    "taxonomic_status": "ACCEPTED",
                    "verified": True,
                },
            )
            if fish_group:
                fish_group.taxonomies.add(taxonomy)
            taxa.append(taxonomy)
            if created:
                self.stdout.write(f"    Created local: {name}")

        # Create invertebrate families
        invert_group = taxon_groups.get("Invertebrates")
        for name in SA_INVERTEBRATE_FAMILIES[:5]:
            taxonomy, created = Taxonomy.objects.get_or_create(
                canonical_name=name,
                defaults={
                    "scientific_name": name,
                    "rank": "FAMILY",
                    "taxonomic_status": "ACCEPTED",
                    "verified": True,
                },
            )
            if invert_group:
                invert_group.taxonomies.add(taxonomy)
            taxa.append(taxonomy)
            if created:
                self.stdout.write(f"    Created local: {name}")

        # Create algae genera
        algae_group = taxon_groups.get("Algae")
        for name in SA_ALGAE_GENERA[:5]:
            taxonomy, created = Taxonomy.objects.get_or_create(
                canonical_name=name,
                defaults={
                    "scientific_name": name,
                    "rank": "GENUS",
                    "taxonomic_status": "ACCEPTED",
                    "verified": True,
                },
            )
            if algae_group:
                algae_group.taxonomies.add(taxonomy)
            taxa.append(taxonomy)
            if created:
                self.stdout.write(f"    Created local: {name}")

        return taxa

    def _create_sites(self, num_sites, location_type, user):
        """Create location sites distributed across South Africa."""
        from bims.models.location_site import LocationSite

        sites = []
        self.stdout.write(f"\nCreating {num_sites} location sites...")

        for i in range(num_sites):
            # Pick a random region or random location
            if random.random() < 0.7:  # 70% near regions
                region = random.choice(SA_REGIONS)
                lat = region["lat"] + random.uniform(
                    -region["radius"], region["radius"]
                )
                lon = region["lon"] + random.uniform(
                    -region["radius"], region["radius"]
                )
                region_name = region["name"]
            else:  # 30% random across SA
                lat = random.uniform(SA_BOUNDS["min_lat"], SA_BOUNDS["max_lat"])
                lon = random.uniform(SA_BOUNDS["min_lon"], SA_BOUNDS["max_lon"])
                region_name = "Remote"

            ecosystem = random.choice(ECOSYSTEM_TYPES)
            site_code = f"DUMMY-{i+1:04d}"

            site = LocationSite.objects.create(
                name=f"{region_name} {ecosystem.title()} Site {i+1}",
                site_code=site_code,
                site_description=f"[DUMMY_DATA] Test site near {region_name}",
                geometry_point=Point(lon, lat, srid=4326),
                latitude=lat,
                longitude=lon,
                location_type=location_type,
                ecosystem_type=ecosystem,
                creator=user,
                owner=user,
                validated=random.random() < 0.8,  # 80% validated
            )

            sites.append(site)

            if (i + 1) % 10 == 0:
                self.stdout.write(f"  Created {i + 1}/{num_sites} sites...")

        self.stdout.write(f"  Created {len(sites)} location sites")
        return sites

    def _create_source_references(self, user):
        """Create source references for dummy data."""
        from bims.models.source_reference import SourceReference

        self.stdout.write("\nCreating source references...")

        source_ref_configs = [
            {
                "source_name": "South African Freshwater Fish Assessment (2024)",
                "note": "[DUMMY_DATA] Test database reference",
            },
            {
                "source_name": "Invertebrate Biodiversity Survey Methods",
                "note": "[DUMMY_DATA] Test report reference",
            },
            {
                "source_name": "Field Guide to Aquatic Ecosystems of Southern Africa",
                "note": "[DUMMY_DATA] Test book reference",
            },
            {
                "source_name": "Journal of Freshwater Ecology",
                "note": "[DUMMY_DATA] Test peer-reviewed reference",
            },
            {
                "source_name": "River Health Programme Data Collection",
                "note": "[DUMMY_DATA] Test unpublished data reference",
            },
            {
                "source_name": "SANBI Biodiversity Database",
                "note": "[DUMMY_DATA] Test SANBI reference",
            },
        ]

        source_refs = []
        for config in source_ref_configs:
            source_ref, created = SourceReference.objects.get_or_create(
                source_name=config["source_name"],
                defaults={
                    "note": config["note"],
                },
            )
            source_refs.append(source_ref)
            if created:
                self.stdout.write(f"  Created: {source_ref.source_name}")

        self.stdout.write(f"  Created {len(source_refs)} source references")
        return source_refs

    def _create_boundaries(self, user):
        """Create boundaries for dummy data."""
        from bims.models.boundary import Boundary
        from bims.models.boundary_type import BoundaryType
        from django.contrib.gis.geos import Polygon, MultiPolygon

        self.stdout.write("\nCreating boundaries...")

        # Create boundary type
        boundary_type, created = BoundaryType.objects.get_or_create(
            name="Province",
            defaults={"level": 1},
        )
        if created:
            self.stdout.write(f"  Created boundary type: {boundary_type.name}")

        # Create some simplified boundary polygons for major SA provinces
        province_bounds = [
            {
                "name": "Western Cape",
                "code": "WC",
                "coords": [(18.0, -34.5), (22.0, -34.5), (22.0, -31.0), (18.0, -31.0), (18.0, -34.5)],
            },
            {
                "name": "Gauteng",
                "code": "GP",
                "coords": [(27.5, -26.5), (29.0, -26.5), (29.0, -25.0), (27.5, -25.0), (27.5, -26.5)],
            },
            {
                "name": "KwaZulu-Natal",
                "code": "KZN",
                "coords": [(29.0, -31.0), (32.5, -31.0), (32.5, -27.0), (29.0, -27.0), (29.0, -31.0)],
            },
        ]

        boundaries = []
        for prov in province_bounds:
            polygon = Polygon(prov["coords"], srid=4326)
            multipoly = MultiPolygon(polygon, srid=4326)
            boundary, created = Boundary.objects.get_or_create(
                name=f"{prov['name']} [DUMMY]",
                code_name=prov["code"],
                type=boundary_type,
                defaults={
                    "geometry": multipoly,
                    "owner": user,
                },
            )
            boundaries.append(boundary)
            if created:
                self.stdout.write(f"  Created boundary: {boundary.name}")

        self.stdout.write(f"  Created {len(boundaries)} boundaries")
        return boundaries

    def _create_site_visits(self, sites, user, num_site_visits):
        """Create site visits (surveys) distributed across sites."""
        from bims.models.survey import Survey

        self.stdout.write(f"\nCreating {num_site_visits} site visits (surveys)...")

        surveys = []
        today = date.today()

        for i in range(num_site_visits):
            site = random.choice(sites)
            survey_date = today - timedelta(days=random.randint(0, 365 * 5))
            collector = random.choice(COLLECTORS)

            survey = Survey.objects.create(
                site=site,
                date=survey_date,
                collector_string=f"{collector} [DUMMY]",
                owner=user,
                collector_user=user,
                validated=site.validated,
            )
            surveys.append(survey)

            if (i + 1) % 1000 == 0:
                self.stdout.write(f"  Created {i + 1}/{num_site_visits} site visits...")

        self.stdout.write(f"  Created {len(surveys)} site visits")
        return surveys

    def _create_records(self, sites, taxa, taxon_groups, user, records_per_site, source_refs=None, existing_surveys=None):
        """Create biological collection records."""
        from bims.models.biological_collection_record import BiologicalCollectionRecord
        from bims.models.survey import Survey

        if not taxa:
            self.stdout.write(self.style.WARNING("No taxa available, skipping records"))
            return

        self.stdout.write(f"\nCreating biological records...")

        total_records = 0
        today = date.today()

        # Group existing surveys by site for efficient lookup
        surveys_by_site = {}
        if existing_surveys:
            for survey in existing_surveys:
                site_id = survey.site_id
                if site_id not in surveys_by_site:
                    surveys_by_site[site_id] = []
                surveys_by_site[site_id].append(survey)

        for site in sites:
            # Vary the number of records per site
            num_records = max(1, int(random.gauss(records_per_site, records_per_site / 2)))
            num_records = min(num_records, records_per_site * 2)  # Cap at 2x average

            # Use existing surveys for this site, or create new ones
            site_surveys = surveys_by_site.get(site.id, [])

            if not site_surveys:
                # Create 1-3 surveys per site if none exist
                num_surveys = random.randint(1, 3)

                for s in range(num_surveys):
                    survey_date = today - timedelta(days=random.randint(0, 365 * 3))
                    collector = random.choice(COLLECTORS)

                    survey = Survey.objects.create(
                        site=site,
                        date=survey_date,
                        collector_string=f"{collector} [DUMMY]",
                        owner=user,
                        collector_user=user,
                        validated=site.validated,
                    )
                    site_surveys.append(survey)

            # Distribute records across surveys
            for _ in range(num_records):
                taxon = random.choice(taxa)
                survey = random.choice(site_surveys)

                # Determine module group based on taxon
                module_group = None
                for group_name, group in taxon_groups.items():
                    if taxon in group.taxonomies.all():
                        module_group = group
                        break

                record = BiologicalCollectionRecord.objects.create(
                    site=site,
                    taxonomy=taxon,
                    original_species_name=taxon.canonical_name,
                    collection_date=survey.date,
                    survey=survey,
                    collector=survey.collector_string,
                    owner=user,
                    collector_user=user,
                    module_group=module_group,
                    abundance_number=random.randint(1, 100) if random.random() < 0.7 else None,
                    present=True,
                    validated=site.validated,
                    notes=f"[DUMMY_DATA] Test record for {taxon.canonical_name}",
                    source_reference=random.choice(source_refs) if source_refs and random.random() < 0.8 else None,
                )

                total_records += 1

        self.stdout.write(f"  Created {total_records} biological records")
