import csv
import io
import json
import os
import shutil
import tempfile
import zipfile as zf
from unittest import mock

from django.db import connection
from django.test import override_settings
from django.utils import timezone
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.utils import schema_context, get_public_schema_name

from django_celery_beat.models import PeriodicTask

from bims.models.gbif_publish import (
    GbifPublish,
    GbifPublishConfig,
    GbifPublishSession,
    PublishPeriod,
    PublishStatus,
)
from bims.models.licence import Licence
from bims.tasks.gbif_publish import run_scheduled_gbif_publish
from bims.tests.model_factories import (
    SourceReferenceF,
    SourceReferenceBibliographyF,
    SourceReferenceDocumentF,
    BiologicalCollectionRecordF,
    SurveyF,
    UserF,
)
from bims.utils.gbif_publish import (
    build_dwca,
    eml_citation,
    eml_author,
    intellectual_rights_text,
    register_dataset,
    publish_gbif_data_with_config,
    LICENSE_URL,
)


# ---------------------------------------------------------------------------
# Shared config helper
# ---------------------------------------------------------------------------

def _make_config(**kwargs):
    defaults = {
        "name": "Test",
        "gbif_api_url": "https://api.gbif-test.org/v1",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
        "export_base_url": "https://example.org",
        "username": "user",
        "password": "pass",
        "publishing_org_key": "org-key",
        "installation_key": "inst-key",
        "is_active": True,
    }
    defaults.update(kwargs)
    return GbifPublishConfig.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Model signal tests
# ---------------------------------------------------------------------------

class GbifPublishModelSignalTests(FastTenantTestCase):

    def test_sync_gbif_publish_periodic_task_daily(self):
        source_reference = SourceReferenceF.create()
        config = _make_config()
        schedule = GbifPublish.objects.create(
            source_reference=source_reference,
            gbif_config=config,
            enabled=True,
            period=PublishPeriod.DAILY,
            run_at=timezone.datetime(2024, 1, 1, 2, 30).time(),
            timezone="UTC",
        )

        with schema_context(get_public_schema_name()):
            task = PeriodicTask.objects.get(
                name=f"GBIF publish: source_reference={source_reference.id} id={schedule.id}"
            )
            self.assertEqual(task.task, "bims.tasks.gbif_publish.run_scheduled_gbif_publish")
            self.assertEqual(json.loads(task.args), [self.tenant.schema_name, schedule.id])
            self.assertTrue(task.enabled)
            self.assertEqual(task.queue, "update")
            self.assertEqual(task.crontab.minute, "30")
            self.assertEqual(task.crontab.hour, "2")

    def test_sync_gbif_publish_periodic_task_custom_cron(self):
        source_reference = SourceReferenceF.create()
        config = _make_config()
        schedule = GbifPublish.objects.create(
            source_reference=source_reference,
            gbif_config=config,
            enabled=False,
            period=PublishPeriod.CUSTOM,
            cron_expression="15 */6 * * *",
            timezone="UTC",
        )

        with schema_context(get_public_schema_name()):
            task = PeriodicTask.objects.get(
                name=f"GBIF publish: source_reference={source_reference.id} id={schedule.id}"
            )
            self.assertFalse(task.enabled)
            self.assertEqual(task.crontab.minute, "15")
            self.assertEqual(task.crontab.hour, "*/6")
            self.assertEqual(task.crontab.day_of_month, "*")
            self.assertEqual(task.crontab.day_of_week, "*")

    def test_gbif_publish_post_delete_removes_task(self):
        source_reference = SourceReferenceF.create()
        config = _make_config()
        schedule = GbifPublish.objects.create(
            source_reference=source_reference,
            gbif_config=config,
            enabled=True,
            period=PublishPeriod.DAILY,
            run_at=timezone.datetime(2024, 1, 1, 2, 0).time(),
            timezone="UTC",
        )

        with schema_context(get_public_schema_name()):
            self.assertTrue(
                PeriodicTask.objects.filter(
                    name=f"GBIF publish: source_reference={source_reference.id} id={schedule.id}"
                ).exists()
            )

        schedule.delete()

        with schema_context(get_public_schema_name()):
            self.assertFalse(
                PeriodicTask.objects.filter(
                    args=json.dumps([self.tenant.schema_name, schedule.id])
                ).exists()
            )


# ---------------------------------------------------------------------------
# Celery task tests
# ---------------------------------------------------------------------------

class GbifPublishTaskTests(FastTenantTestCase):

    def _create_schedule(self, **kwargs):
        source_reference = kwargs.pop("source_reference", SourceReferenceBibliographyF.create())
        config = kwargs.pop("gbif_config", _make_config())
        defaults = {
            "source_reference": source_reference,
            "gbif_config": config,
            "enabled": True,
            "period": PublishPeriod.DAILY,
            "run_at": timezone.datetime(2024, 1, 1, 2, 0).time(),
            "timezone": "UTC",
        }
        defaults.update(kwargs)
        return GbifPublish.objects.create(**defaults)

    def test_task_skips_when_locked(self):
        schedule = self._create_schedule()
        with mock.patch("bims.tasks.gbif_publish.pg_advisory_lock") as lock_mock:
            lock_mock.return_value.__enter__.return_value = False
            lock_mock.return_value.__exit__.return_value = None
            result = run_scheduled_gbif_publish(self.tenant.schema_name, schedule.id)

        self.assertEqual(result["status"], "skipped_locked")
        self.assertFalse(GbifPublishSession.objects.exists())

    def test_task_returns_disabled(self):
        schedule = self._create_schedule(enabled=False)
        with mock.patch("bims.tasks.gbif_publish.pg_advisory_lock") as lock_mock:
            lock_mock.return_value.__enter__.return_value = True
            lock_mock.return_value.__exit__.return_value = None
            result = run_scheduled_gbif_publish(self.tenant.schema_name, schedule.id)

        self.assertEqual(result["status"], "disabled")
        self.assertFalse(GbifPublishSession.objects.exists())

    def test_task_success_updates_session_and_schedule(self):
        schedule = self._create_schedule()
        with mock.patch("bims.tasks.gbif_publish.pg_advisory_lock") as lock_mock:
            lock_mock.return_value.__enter__.return_value = True
            lock_mock.return_value.__exit__.return_value = None

            with mock.patch(
                "bims.tasks.gbif_publish.publish_gbif_data_with_config",
                return_value={
                    "dataset_key": "dataset-123",
                    "records_published": 3,
                    "archive_url": "https://example.org/media/dwca.zip",
                },
            ):
                result = run_scheduled_gbif_publish(self.tenant.schema_name, schedule.id)

        self.assertEqual(result["status"], "success")
        session = GbifPublishSession.objects.get(id=result["session_id"])
        self.assertEqual(session.status, PublishStatus.SUCCESS)
        self.assertEqual(session.dataset_key, "dataset-123")
        schedule.refresh_from_db()
        self.assertIsNotNone(schedule.last_publish)

    def test_task_no_records_marks_session(self):
        schedule = self._create_schedule()
        with mock.patch("bims.tasks.gbif_publish.pg_advisory_lock") as lock_mock:
            lock_mock.return_value.__enter__.return_value = True
            lock_mock.return_value.__exit__.return_value = None

            with mock.patch(
                "bims.tasks.gbif_publish.publish_gbif_data_with_config",
                side_effect=ValueError("No records to publish"),
            ):
                result = run_scheduled_gbif_publish(self.tenant.schema_name, schedule.id)

        self.assertEqual(result["status"], "no_records")
        session = GbifPublishSession.objects.get(id=result["session_id"])
        self.assertEqual(session.status, PublishStatus.NO_RECORDS)
        self.assertIn("No records to publish", session.error_message)

    def test_task_error_marks_session(self):
        schedule = self._create_schedule()
        with mock.patch("bims.tasks.gbif_publish.pg_advisory_lock") as lock_mock:
            lock_mock.return_value.__enter__.return_value = True
            lock_mock.return_value.__exit__.return_value = None

            with mock.patch(
                "bims.tasks.gbif_publish.publish_gbif_data_with_config",
                side_effect=RuntimeError("Boom"),
            ):
                result = run_scheduled_gbif_publish(self.tenant.schema_name, schedule.id)

        self.assertEqual(result["status"], "error")
        session = GbifPublishSession.objects.get(id=result["session_id"])
        self.assertEqual(session.status, PublishStatus.ERROR)
        self.assertIn("Boom", session.error_message)


# ---------------------------------------------------------------------------
# API / build_dwca tests
# ---------------------------------------------------------------------------

class GbifPublishApiTests(FastTenantTestCase):

    def _make_record(self, source_reference, **kwargs):
        survey = SurveyF.create(validated=True)
        return BiologicalCollectionRecordF.create(
            survey=survey,
            source_reference=source_reference,
            data_type="public",
            **kwargs,
        )

    def _read_occurrence_rows(self, zip_path):
        with zf.ZipFile(zip_path) as z:
            content = z.read("occurrence.txt").decode("utf-8")
        reader = csv.DictReader(io.StringIO(content), delimiter="\t")
        return list(reader)

    def _read_eml(self, zip_path):
        with zf.ZipFile(zip_path) as z:
            return z.read("eml.xml").decode("utf-8")

    # -- register_dataset error handling --

    def test_register_dataset_401(self):
        config = _make_config()
        response = mock.Mock()
        response.status_code = 401
        response.raise_for_status = mock.Mock()
        response.json.return_value = ""

        with mock.patch("bims.utils.gbif_publish.requests.post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "401 Unauthorized"):
                register_dataset(config, "title", "desc")

    def test_register_dataset_403(self):
        config = _make_config()
        response = mock.Mock()
        response.status_code = 403
        response.raise_for_status = mock.Mock()
        response.json.return_value = ""

        with mock.patch("bims.utils.gbif_publish.requests.post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "403 Forbidden"):
                register_dataset(config, "title", "desc")

    # -- build_dwca: archive URL --

    def test_build_dwca_uses_export_base_url(self):
        source_reference = SourceReferenceF.create()
        record = self._make_record(source_reference)
        config = _make_config(export_base_url="https://example.org")
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, archive_url, written_ids = build_dwca(config, [record], source_reference)

        self.assertTrue(os.path.exists(zip_path))
        self.assertIn(record.id, written_ids)
        self.assertTrue(archive_url.startswith("https://example.org/media/"))

    # -- EML title / description --

    def test_build_dwca_title_is_source_reference_title(self):
        source_reference = SourceReferenceF.create()
        source_reference.source_name = "My Reference Title"
        source_reference.save()
        record = self._make_record(source_reference)
        config = _make_config(export_base_url="https://example.org")
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, _, _ = build_dwca(config, [record], source_reference)

        eml = self._read_eml(zip_path)
        self.assertIn("My Reference Title", eml)
        self.assertNotIn("UTC", eml.split("<title>")[1].split("</title>")[0])

    def test_build_dwca_description_format(self):
        source_reference = SourceReferenceF.create()
        source_reference.source_name = "Fish Survey 2022"
        source_reference.save()
        record = self._make_record(source_reference)
        config = _make_config(export_base_url="https://example.org")
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/", SITE_NAME="FBIS"):
            zip_path, _, _ = build_dwca(config, [record], source_reference)

        eml = self._read_eml(zip_path)
        self.assertIn(
            "Occurrence dataset for Fish Survey 2022 uploaded to FBIS.",
            eml,
        )

    # -- occurrenceID tenant prefix --

    def test_occurrence_id_uses_tenant_name(self):
        source_reference = SourceReferenceF.create()
        record = self._make_record(source_reference)
        config = _make_config(export_base_url="https://example.org")
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, _, written_ids = build_dwca(config, [record], source_reference)

        rows = self._read_occurrence_rows(zip_path)
        self.assertTrue(len(rows) > 0)
        tenant = connection.schema_name
        for row in rows:
            self.assertTrue(
                row["occurrenceID"].startswith(f"{tenant}:"),
                f"Expected occurrenceID to start with '{tenant}:', got '{row['occurrenceID']}'",
            )

    # -- abundance type mapping --

    def _make_record_with_abundance(self, source_reference, abundance_name, abundance_number):
        from bims.models.abundance_type import AbundanceType
        abundance_type, _ = AbundanceType.objects.get_or_create(name=abundance_name)
        return self._make_record(
            source_reference,
            abundance_type=abundance_type,
            abundance_number=abundance_number,
        )

    def test_abundance_number_type(self):
        source_reference = SourceReferenceF.create()
        record = self._make_record_with_abundance(source_reference, "Number", 5)
        config = _make_config(export_base_url="https://example.org")
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, _, _ = build_dwca(config, [record], source_reference)

        rows = self._read_occurrence_rows(zip_path)
        self.assertAlmostEqual(float(rows[0]["individualCount"]), 5.0)
        self.assertAlmostEqual(float(rows[0]["organismQuantity"]), 5.0)
        self.assertEqual(rows[0]["organismQuantityType"], "individuals")

    def test_abundance_percentage_type(self):
        source_reference = SourceReferenceF.create()
        record = self._make_record_with_abundance(source_reference, "Percentage", 30)
        config = _make_config(export_base_url="https://example.org")
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, _, _ = build_dwca(config, [record], source_reference)

        rows = self._read_occurrence_rows(zip_path)
        self.assertEqual(rows[0]["individualCount"], "")
        self.assertEqual(rows[0]["organismQuantityType"], "% cover")

    def test_abundance_density_m2_type(self):
        source_reference = SourceReferenceF.create()
        record = self._make_record_with_abundance(source_reference, "Density (m2)", 12)
        config = _make_config(export_base_url="https://example.org")
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, _, _ = build_dwca(config, [record], source_reference)

        rows = self._read_occurrence_rows(zip_path)
        self.assertEqual(rows[0]["individualCount"], "")
        self.assertEqual(rows[0]["organismQuantityType"], "individuals/m2")

    # -- intellectualRights --

    def test_intellectual_rights_default(self):
        text = intellectual_rights_text(None)
        self.assertIn("Creative Commons CCZero 1.0 License", text)
        self.assertIn(LICENSE_URL, text)
        self.assertTrue(text.startswith("This work is licensed under a "))

    def test_intellectual_rights_with_licence(self):
        licence = Licence(name="CC BY 4.0", url="https://creativecommons.org/licenses/by/4.0/legalcode")
        text = intellectual_rights_text(licence)
        self.assertEqual(
            text,
            "This work is licensed under a CC BY 4.0 https://creativecommons.org/licenses/by/4.0/legalcode.",
        )

    def test_eml_multiple_licences(self):
        source_reference = SourceReferenceF.create()
        lic1 = Licence.objects.create(name="CC BY 4.0", identifier="cc-by-4", url="https://creativecommons.org/licenses/by/4.0/legalcode")
        lic2 = Licence.objects.create(name="CC0 1.0", identifier="cc0-1", url="https://creativecommons.org/publicdomain/zero/1.0/legalcode")
        record1 = self._make_record(source_reference, licence=lic1)
        record2 = self._make_record(source_reference, licence=lic2)
        config = _make_config(export_base_url="https://example.org")
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, _, _ = build_dwca(config, [record1, record2], source_reference)

        eml = self._read_eml(zip_path)
        self.assertIn("CC BY 4.0", eml)
        self.assertIn("CC0 1.0", eml)
        self.assertEqual(eml.count("<para>This work is licensed under"), 2)

    # -- eml_author: org and role --

    def test_eml_author_includes_organization_and_role(self):
        from bims.models.profile import Role, Profile as BimsProfile
        user = UserF.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
        )
        user.organization = "University of Cape Town"
        user.save()
        role, _ = Role.objects.get_or_create(
            name="researcher", defaults={"display_name": "Researcher"}
        )
        bims_profile, _ = BimsProfile.objects.get_or_create(user=user)
        bims_profile.role = role
        bims_profile.save()

        snippet = eml_author(user)
        self.assertIn("Jane", snippet)
        self.assertIn("Smith", snippet)
        self.assertIn("University of Cape Town", snippet)
        self.assertIn("<positionName>Researcher</positionName>", snippet)
        self.assertIn("jane@example.com", snippet)

    # -- eml_citation --

    def test_eml_citation_bibliography(self):
        source_reference = SourceReferenceBibliographyF.create()
        source_reference.source.doi = "10.1038/ismej.2011.170"
        source_reference.source.save()

        result = eml_citation(source_reference)

        self.assertIn('identifier="10.1038/ismej.2011.170"', result)
        self.assertIn("doi:10.1038/ismej.2011.170", result)
        self.assertTrue(result.startswith("<citation"))
        self.assertTrue(result.endswith("</citation>"))

    def test_eml_citation_document(self):
        source_reference = SourceReferenceDocumentF.create()
        source_reference.source.doc_url = "https://example.org/doc.pdf"
        source_reference.source.save()

        result = eml_citation(source_reference)

        self.assertIn('identifier="https://example.org/doc.pdf"', result)
        self.assertTrue(result.startswith("<citation"))

    def test_eml_citation_plain_reference_returns_empty(self):
        source_reference = SourceReferenceF.create()
        self.assertEqual(eml_citation(source_reference), "")

    def test_eml_citation_in_additional_metadata(self):
        source_reference = SourceReferenceBibliographyF.create()
        source_reference.source.doi = "10.9999/test"
        source_reference.source.save()
        record = self._make_record(source_reference)
        config = _make_config(export_base_url="https://example.org")
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, _, _ = build_dwca(config, [record], source_reference)

        eml = self._read_eml(zip_path)
        self.assertIn("<additionalMetadata>", eml)
        self.assertIn("<citation", eml)
        self.assertIn("10.9999/test", eml)

    # -- publish_gbif_data_with_config --

    def test_publish_gbif_data_with_config_updates_records(self):
        source_reference = SourceReferenceF.create()
        record = self._make_record(source_reference)
        config = _make_config()

        with mock.patch(
            "bims.utils.gbif_publish.build_dwca",
            return_value=("/tmp/dwca.zip", "https://example.org/media/dwca.zip", [record.id]),
        ), mock.patch(
            "bims.utils.gbif_publish.register_dataset",
            return_value="dataset-xyz",
        ), mock.patch(
            "bims.utils.gbif_publish.add_endpoint",
            return_value=None,
        ):
            result = publish_gbif_data_with_config(config, source_reference=source_reference)

        record.refresh_from_db()
        self.assertEqual(record.dataset_key, "dataset-xyz")
        self.assertEqual(result["dataset_key"], "dataset-xyz")
        self.assertEqual(result["records_published"], 1)


# ---------------------------------------------------------------------------
# Crontab tests
# ---------------------------------------------------------------------------

class GbifPublishCrontabTests(FastTenantTestCase):

    def test_monthly_crontab_defaults_day_of_month(self):
        source_reference = SourceReferenceF.create()
        config = _make_config()
        schedule = GbifPublish.objects.create(
            source_reference=source_reference,
            gbif_config=config,
            enabled=True,
            period=PublishPeriod.MONTHLY,
            run_at=timezone.datetime(2024, 1, 1, 2, 0).time(),
            day_of_month=None,
            timezone="UTC",
        )

        with schema_context(get_public_schema_name()):
            task = PeriodicTask.objects.get(
                name=f"GBIF publish: source_reference={source_reference.id} id={schedule.id}"
            )
            self.assertEqual(task.crontab.day_of_month, "1")
