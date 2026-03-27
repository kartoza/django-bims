import json
import os
import shutil
import tempfile
from unittest import mock

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
from bims.tasks.gbif_publish import run_scheduled_gbif_publish
from bims.tests.model_factories import (
    SourceReferenceF,
    BiologicalCollectionRecordF,
    SurveyF, SourceReferenceBibliographyF,
)
from bims.utils.gbif_publish import (
    build_dwca,
    register_dataset,
    publish_gbif_data_with_config,
)


class GbifPublishModelSignalTests(FastTenantTestCase):
    def _create_config(self, **kwargs):
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

    def test_sync_gbif_publish_periodic_task_daily(self):
        source_reference = SourceReferenceF.create()
        config = self._create_config()
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
        config = self._create_config()
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
        config = self._create_config()
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


class GbifPublishTaskTests(FastTenantTestCase):
    def _create_config(self, **kwargs):
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

    def _create_schedule(self, **kwargs):
        source_reference = SourceReferenceBibliographyF.create()
        config = kwargs.pop("gbif_config", self._create_config())
        defaults = {
            "source_reference": source_reference,
            "gbif_config": config,
            "enabled": True,
            "period": PublishPeriod.DAILY,
            "run_at": timezone.datetime(2024, 1, 1, 2, 0).time(),
            "timezone": "UTC",
        }
        defaults.update(kwargs)
        schedule = GbifPublish.objects.create(**defaults)
        return schedule

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


class GbifPublishApiTests(FastTenantTestCase):
    def _create_config(self, **kwargs):
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

    def _make_record(self, source_reference):
        survey = SurveyF.create(validated=True)
        record = BiologicalCollectionRecordF.create(
            survey=survey,
            source_reference=source_reference,
            data_type="public",
        )
        return record

    def testregister_dataset_401(self):
        config = self._create_config()

        response = mock.Mock()
        response.status_code = 401
        response.raise_for_status = mock.Mock()
        response.json.return_value = ""

        with mock.patch("bims.utils.gbif_publish.requests.post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "401 Unauthorized"):
                register_dataset(config, "title", "desc")

    def testregister_dataset_403(self):
        config = self._create_config()

        response = mock.Mock()
        response.status_code = 403
        response.raise_for_status = mock.Mock()
        response.json.return_value = ""

        with mock.patch("bims.utils.gbif_publish.requests.post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "403 Forbidden"):
                register_dataset(config, "title", "desc")

    def test_build_dwca_uses_export_base_url(self):
        source_reference = SourceReferenceF.create()
        record = self._make_record(source_reference)
        config = self._create_config(export_base_url="https://example.org")

        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, archive_url, written_ids = build_dwca(
                config, [record], source_reference
            )

        self.assertTrue(os.path.exists(zip_path))
        self.assertIn(record.id, written_ids)
        self.assertTrue(archive_url.startswith("https://example.org/media/"))

    def test_build_dwca_title_is_source_reference_title(self):
        source_reference = SourceReferenceF.create()
        source_reference.source_name = "My Reference Title"
        source_reference.save()
        record = self._make_record(source_reference)
        config = self._create_config(export_base_url="https://example.org")

        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, archive_url, written_ids = build_dwca(
                config, [record], source_reference
            )

        import zipfile as zf
        with zf.ZipFile(zip_path) as z:
            eml_content = z.read("eml.xml").decode("utf-8")

        self.assertIn("My Reference Title", eml_content)
        self.assertNotIn("UTC", eml_content.split("<title>")[1].split("</title>")[0])

    def test_build_dwca_description_format(self):
        source_reference = SourceReferenceF.create()
        source_reference.source_name = "Fish Survey 2022"
        source_reference.save()
        record = self._make_record(source_reference)
        config = self._create_config(export_base_url="https://example.org")

        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/", SITE_NAME="FBIS"):
            zip_path, archive_url, written_ids = build_dwca(
                config, [record], source_reference
            )

        import zipfile as zf
        with zf.ZipFile(zip_path) as z:
            eml_content = z.read("eml.xml").decode("utf-8")

        self.assertIn(
            "Occurrence dataset for Fish Survey 2022 uploaded to FBIS.",
            eml_content
        )

    def test_publish_gbif_data_with_config_updates_records(self):
        source_reference = SourceReferenceF.create()
        record = self._make_record(source_reference)
        config = self._create_config()

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


class GbifPublishCrontabTests(FastTenantTestCase):
    def _create_config(self, **kwargs):
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

    def test_monthly_crontab_defaults_day_of_month(self):
        source_reference = SourceReferenceF.create()
        config = self._create_config()
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
