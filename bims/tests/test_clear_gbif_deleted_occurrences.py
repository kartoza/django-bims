# bims/tests/test_clear_gbif_deleted_occurrences.py
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import override_settings
from django.utils import timezone
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.utils import schema_context, get_public_schema_name

from bims.models import BiologicalCollectionRecord
from bims.tests.model_factories import LocationSiteF, SurveyF, UserF
from bims.tasks.gbif_deletions import clear_gbif_deleted_occurrences

from tenants.models import Domain

DELETED_UPSTREAM = {"DEL1", "DEL2"}


def _fake_occurrence_deleted(session, gbif_id, timeout):
    """Pretend GBIF returned 404 for the ids we mark as deleted."""
    return gbif_id in DELETED_UPSTREAM


@override_settings(
    DEFAULT_FROM_EMAIL="noreply@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class ClearGbifDeletedOccurrencesTests(FastTenantTestCase):
    def setUp(self):
        super().setUp()
        self.admin = UserF.create(is_superuser=True, email="admin@example.com")

        with schema_context(get_public_schema_name()):
            Domain.objects.create(
                tenant=self.tenant, domain="fast_test", is_primary=True
            )

        self.site = LocationSiteF.create(name="Site")
        self.survey = SurveyF.create(site=self.site)

        # Two GBIF records deleted upstream, one still alive.
        self.deleted1 = self._make_record("DEL1", "Deleted One")
        self.deleted2 = self._make_record("DEL2", "Deleted Two")
        self.alive = self._make_record("ALIVE1", "Alive One")

        mail.outbox[:] = []

    def _make_record(self, upstream_id, name):
        record = BiologicalCollectionRecord.objects.create(
            site=self.site,
            survey=self.survey,
            original_species_name=name,
            source_collection="GBIF",
            upstream_id=upstream_id,
            dataset_key=f"dataset-{upstream_id}",
        )
        return record

    def _set_modified(self, record, when):
        # Bypass save() (which restamps modified_date) via update().
        BiologicalCollectionRecord.objects.filter(id=record.id).update(
            modified_date=when)

    # ------------------------------------------------------------------ #
    # DRY RUN: reports, attaches CSV, deletes nothing.
    # ------------------------------------------------------------------ #
    @patch("bims.tasks.gbif_deletions._occurrence_deleted",
           side_effect=_fake_occurrence_deleted)
    def test_dry_run_reports_and_attaches_csv(self, _mock):
        res = clear_gbif_deleted_occurrences(dry_run=True, stale_days=0)

        self.assertTrue(res["ok"])
        self.assertEqual(res["checked"], 3)
        self.assertEqual(res["to_delete"], 2)
        self.assertEqual(res["deleted"], 0)

        # Nothing deleted.
        self.assertEqual(BiologicalCollectionRecord.objects.count(), 3)

        # One email with a CSV attachment listing the affected records.
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn("[fast_test]", msg.subject)
        self.assertIn("(DRY RUN)", msg.subject)
        self.assertEqual(len(msg.attachments), 1)
        filename, content, mimetype = msg.attachments[0]
        self.assertEqual(filename, "gbif_deleted_occurrences.csv")
        self.assertEqual(mimetype, "text/csv")
        self.assertIn("DEL1", content)
        self.assertIn("DEL2", content)
        self.assertNotIn("ALIVE1", content)

    # ------------------------------------------------------------------ #
    # REAL RUN: deletes only the upstream-deleted records.
    # ------------------------------------------------------------------ #
    @patch("bims.tasks.gbif_deletions._occurrence_deleted",
           side_effect=_fake_occurrence_deleted)
    def test_real_run_deletes_only_upstream_deleted(self, _mock):
        res = clear_gbif_deleted_occurrences(dry_run=False, stale_days=0)

        self.assertEqual(res["to_delete"], 2)
        self.assertEqual(res["deleted"], 2)

        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(
                id__in=[self.deleted1.id, self.deleted2.id]).exists())
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(id=self.alive.id).exists())

        # Real run: no CSV attached.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].attachments), 0)
        self.assertNotIn("(DRY RUN)", mail.outbox[0].subject)

    # ------------------------------------------------------------------ #
    # Alive records are marked as freshly checked (modified_date bumped).
    # ------------------------------------------------------------------ #
    @patch("bims.tasks.gbif_deletions._occurrence_deleted",
           side_effect=_fake_occurrence_deleted)
    def test_alive_record_modified_date_is_bumped(self, _mock):
        old = timezone.now() - timedelta(days=100)
        self._set_modified(self.alive, old)

        clear_gbif_deleted_occurrences(dry_run=True, stale_days=0)

        self.alive.refresh_from_db()
        self.assertGreater(
            self.alive.modified_date, timezone.now() - timedelta(minutes=1))

    # ------------------------------------------------------------------ #
    # stale_days skips records modified more recently than the cutoff.
    # ------------------------------------------------------------------ #
    @patch("bims.tasks.gbif_deletions._occurrence_deleted",
           side_effect=_fake_occurrence_deleted)
    def test_stale_days_skips_recent_records(self, _mock):
        # deleted1 is stale (old), deleted2 is recent; alive is recent.
        self._set_modified(self.deleted1, timezone.now() - timedelta(days=60))
        self._set_modified(self.deleted2, timezone.now())
        self._set_modified(self.alive, timezone.now())

        res = clear_gbif_deleted_occurrences(dry_run=False, stale_days=30)

        # Only the stale, upstream-deleted record is checked and removed.
        self.assertEqual(res["checked"], 1)
        self.assertEqual(res["deleted"], 1)
        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(id=self.deleted1.id).exists())
        self.assertTrue(
            BiologicalCollectionRecord.objects.filter(id=self.deleted2.id).exists())
