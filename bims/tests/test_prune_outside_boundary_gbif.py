# bims/tests/test_prune_outside_boundary_gbif.py
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.gis.geos import GEOSGeometry
from django.core import mail
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from django_tenants.utils import schema_context, get_public_schema_name

from bims.models import LocationSite, Survey, BiologicalCollectionRecord
from bims.tests.model_factories import LocationSiteF, SurveyF, UserF
from bims.tasks.prune_outside_boundary import prune_outside_boundary_gbif

# Domain model lives in "public" schema in most django-tenants setups
from tenants.models import Domain


@override_settings(
    DEFAULT_FROM_EMAIL="noreply@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class PruneOutsideBoundaryGbifTests(FastTenantTestCase):
    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)

        # Superuser with email to receive reports
        self.admin = UserF.create(is_superuser=True, email="admin@example.com")

        # Create a primary domain for this tenant in PUBLIC schema
        with schema_context(get_public_schema_name()):
            Domain.objects.create(
                tenant=self.tenant, domain="fast_test", is_primary=True
            )

        # Boundary: small square around (0,0)~(1,1)
        self.boundary_geom = GEOSGeometry(
            "MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))", srid=4326
        )

        # Patch preferences.SiteSetting.site_boundary to a simple object with .geometry
        self.pref_patcher = patch(
            "bims.tasks.prune_outside_boundary.preferences",
            new=SimpleNamespace(
                SiteSetting=SimpleNamespace(
                    site_boundary=SimpleNamespace(geometry=self.boundary_geom)
                )
            ),
        )
        self.pref_patcher.start()

        # --- Test data -------------------------------------------------
        # Inside site (should be ignored by the task)
        self.site_inside = LocationSiteF.create(name="Inside")
        self.site_inside.geometry_point = GEOSGeometry("POINT(0.5 0.5)", srid=4326)
        self.site_inside.save()
        self.svy_inside = SurveyF.create(site=self.site_inside)
        BiologicalCollectionRecord.objects.create(
            site=self.site_inside,
            survey=self.svy_inside,
            original_species_name="InsideSpecies",
            source_collection="GBIF",  # should not be touched (inside boundary)
        )

        # Outside site 1: only GBIF data → survey & site should be removed
        self.site_out1 = LocationSiteF.create(name="Outside1")
        self.site_out1.geometry_point = GEOSGeometry("POINT(5 5)", srid=4326)
        self.site_out1.save()
        self.svy_out1 = SurveyF.create(site=self.site_out1)
        self.bcr_out1_gbif = BiologicalCollectionRecord.objects.create(
            site=self.site_out1,
            survey=self.svy_out1,
            original_species_name="Out1SpeciesGBIF",
            source_collection="GBIF",
        )

        # Outside site 2: GBIF + non-GBIF → delete GBIF only, keep survey & site
        self.site_out2 = LocationSiteF.create(name="Outside2")
        self.site_out2.geometry_point = GEOSGeometry("POINT(5.1 5.1)", srid=4326)
        self.site_out2.save()
        self.svy_out2 = SurveyF.create(site=self.site_out2)
        self.bcr_out2_gbif = BiologicalCollectionRecord.objects.create(
            site=self.site_out2,
            survey=self.svy_out2,
            original_species_name="Out2GBIF",
            source_collection="GBIF",
        )
        self.bcr_out2_non = BiologicalCollectionRecord.objects.create(
            site=self.site_out2,
            survey=self.svy_out2,
            original_species_name="Out2Local",
            source_collection="bims",  # non-GBIF
        )

        # Reset mailbox
        mail.outbox[:] = []

    def tearDown(self):
        self.pref_patcher.stop()
        super().tearDown()

    # ------------------------------------------------------------------ #
    # DRY RUN: counts match expectations; subject uses domain
    # ------------------------------------------------------------------ #
    def test_dry_run_counts_and_subject_domain(self):
        res = prune_outside_boundary_gbif(dry_run=True, delete_empty_sites=True)

        # Outside sites are out1 & out2 (2 total)
        self.assertTrue(res["ok"])
        self.assertEqual(res["outside_sites"], 2)

        # GBIF occurrences to delete: out1:1 + out2:1 = 2
        self.assertEqual(res["gbif_occ_deleted"], 2)

        # Surveys that would be deleted: out1's survey only (no non-GBIF) = 1
        self.assertEqual(res["surveys_deleted"], 1)

        # Sites that would be deleted: out1 only (no non-GBIF left) = 1
        self.assertEqual(res["sites_deleted"], 1)

        # Email sent to superusers
        self.assertEqual(len(mail.outbox), 1)
        subj = mail.outbox[0].subject
        body = mail.outbox[0].body

        self.assertIn("[fast_test]", subj)
        self.assertIn("Outside-boundary GBIF cleanup (DRY RUN)", subj)
        self.assertIn("Automatic cleanup completed", body)
        self.assertIn("GBIF occurrences", body)

        # Ensure DB not modified in dry run
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(id=self.bcr_out1_gbif.id).exists()
        )
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(id=self.bcr_out2_gbif.id).exists()
        )
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(id=self.bcr_out2_non.id).exists()
        )
        self.assertTrue(LocationSite.objects.filter(id=self.site_out1.id).exists())
        self.assertTrue(LocationSite.objects.filter(id=self.site_out2.id).exists())
        self.assertTrue(Survey.objects.filter(id=self.svy_out1.id).exists())
        self.assertTrue(Survey.objects.filter(id=self.svy_out2.id).exists())

    # ------------------------------------------------------------------ #
    # REAL RUN: actually deletes GBIF outside; removes empty surveys/sites
    # ------------------------------------------------------------------ #
    def test_real_run_deletes_expected_things(self):
        res = prune_outside_boundary_gbif(dry_run=False, delete_empty_sites=True)

        self.assertTrue(res["ok"])
        self.assertEqual(res["outside_sites"], 2)
        self.assertEqual(res["gbif_occ_deleted"], 2)
        self.assertEqual(res["surveys_deleted"], 1)  # out1 only
        self.assertEqual(res["sites_deleted"], 1)    # out1 only

        # out1: GBIF removed, survey removed, site removed
        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(id=self.bcr_out1_gbif.id).exists()
        )
        self.assertFalse(Survey.objects.filter(id=self.svy_out1.id).exists())
        self.assertFalse(LocationSite.objects.filter(id=self.site_out1.id).exists())

        # out2: GBIF removed, but non-GBIF remains; survey & site remain
        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(id=self.bcr_out2_gbif.id).exists()
        )
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(id=self.bcr_out2_non.id).exists()
        )
        self.assertTrue(Survey.objects.filter(id=self.svy_out2.id).exists())
        self.assertTrue(LocationSite.objects.filter(id=self.site_out2.id).exists())

        # inside: untouched
        self.assertTrue(Survey.objects.filter(id=self.svy_inside.id).exists())
        self.assertEqual(
            BiologicalCollectionRecord.objects.filter(site=self.site_inside).count(), 1
        )

        # One email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("[fast_test] Outside-boundary GBIF cleanup", mail.outbox[0].subject)
        self.assertNotIn("(DRY RUN)", mail.outbox[0].subject)

    # ------------------------------------------------------------------ #
    # Abort path: no boundary configured → email & ok=False
    # ------------------------------------------------------------------ #
    def test_abort_when_no_boundary_emails_and_returns_error(self):
        # Replace preferences with None boundary
        with patch(
            "bims.tasks.prune_outside_boundary.preferences",
            new=SimpleNamespace(SiteSetting=SimpleNamespace(site_boundary=None)),
        ):
            mail.outbox[:] = []
            res = prune_outside_boundary_gbif(dry_run=True, delete_empty_sites=True)

        self.assertFalse(res["ok"])
        self.assertIn("error", res)

        # Aborted email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("[fast_test] Outside-boundary cleanup aborted", mail.outbox[0].subject)
        self.assertIn("Site boundary not configured", mail.outbox[0].body)
        