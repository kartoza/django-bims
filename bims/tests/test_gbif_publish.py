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
    TaxonGroupF,
    BiologicalCollectionRecordF,
    SurveyF,
)
from bims.utils.gbif_publish import (
    _build_dwca_with_config,
    _register_dataset_with_config,
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
        module_group = TaxonGroupF.create()
        config = self._create_config()
        schedule = GbifPublish.objects.create(
            module_group=module_group,
            gbif_config=config,
            enabled=True,
            period=PublishPeriod.DAILY,
            run_at=timezone.datetime(2024, 1, 1, 2, 30).time(),
            timezone="UTC",
        )

        with schema_context(get_public_schema_name()):
            task = PeriodicTask.objects.get(
                name=f"GBIF publish: taxon_group={module_group.id} id={schedule.id}"
            )
            self.assertEqual(task.task, "bims.tasks.gbif_publish.run_scheduled_gbif_publish")
            self.assertEqual(json.loads(task.args), [self.tenant.schema_name, schedule.id])
            self.assertTrue(task.enabled)
            self.assertEqual(task.queue, "update")
            self.assertEqual(task.crontab.minute, "30")
            self.assertEqual(task.crontab.hour, "2")

    def test_sync_gbif_publish_periodic_task_custom_cron(self):
        module_group = TaxonGroupF.create()
        config = self._create_config()
        schedule = GbifPublish.objects.create(
            module_group=module_group,
            gbif_config=config,
            enabled=False,
            period=PublishPeriod.CUSTOM,
            cron_expression="15 */6 * * *",
            timezone="UTC",
        )

        with schema_context(get_public_schema_name()):
            task = PeriodicTask.objects.get(
                name=f"GBIF publish: taxon_group={module_group.id} id={schedule.id}"
            )
            self.assertFalse(task.enabled)
            self.assertEqual(task.crontab.minute, "15")
            self.assertEqual(task.crontab.hour, "*/6")
            self.assertEqual(task.crontab.day_of_month, "*")
            self.assertEqual(task.crontab.day_of_week, "*")

    def test_gbif_publish_post_delete_removes_task(self):
        module_group = TaxonGroupF.create()
        config = self._create_config()
        schedule = GbifPublish.objects.create(
            module_group=module_group,
            gbif_config=config,
            enabled=True,
            period=PublishPeriod.DAILY,
            run_at=timezone.datetime(2024, 1, 1, 2, 0).time(),
            timezone="UTC",
        )

        with schema_context(get_public_schema_name()):
            self.assertTrue(
                PeriodicTask.objects.filter(
                    name=f"GBIF publish: taxon_group={module_group.id} id={schedule.id}"
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
        module_group = kwargs.pop("module_group", TaxonGroupF.create())
        config = kwargs.pop("gbif_config", self._create_config())
        defaults = {
            "module_group": module_group,
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

    def _make_record(self, module_group):
        survey = SurveyF.create(validated=True)
        record = BiologicalCollectionRecordF.create(
            survey=survey,
            module_group=module_group,
            data_type="public",
        )
        return record

    def test_register_dataset_with_config_401(self):
        config = self._create_config()

        response = mock.Mock()
        response.status_code = 401
        response.raise_for_status = mock.Mock()
        response.json.return_value = ""

        with mock.patch("bims.utils.gbif_publish.requests.post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "401 Unauthorized"):
                _register_dataset_with_config(config, "title", "desc")

    def test_register_dataset_with_config_403(self):
        config = self._create_config()

        response = mock.Mock()
        response.status_code = 403
        response.raise_for_status = mock.Mock()
        response.json.return_value = ""

        with mock.patch("bims.utils.gbif_publish.requests.post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "403 Forbidden"):
                _register_dataset_with_config(config, "title", "desc")

    def test_build_dwca_with_config_uses_export_base_url(self):
        module_group = TaxonGroupF.create()
        record = self._make_record(module_group)
        config = self._create_config(export_base_url="https://example.org")

        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL="/media/"):
            zip_path, archive_url, written_ids = _build_dwca_with_config(
                config, [record], module_group
            )

        self.assertTrue(os.path.exists(zip_path))
        self.assertIn(record.id, written_ids)
        self.assertTrue(archive_url.startswith("https://example.org/media/"))

    def test_publish_gbif_data_with_config_updates_records(self):
        module_group = TaxonGroupF.create()
        record = self._make_record(module_group)
        config = self._create_config()

        with mock.patch(
            "bims.utils.gbif_publish._build_dwca_with_config",
            return_value=("/tmp/dwca.zip", "https://example.org/media/dwca.zip", [record.id]),
        ), mock.patch(
            "bims.utils.gbif_publish._register_dataset_with_config",
            return_value="dataset-xyz",
        ), mock.patch(
            "bims.utils.gbif_publish._add_endpoint_with_config",
            return_value=None,
        ):
            result = publish_gbif_data_with_config(config, module_group=module_group)

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
        module_group = TaxonGroupF.create()
        config = self._create_config()
        schedule = GbifPublish.objects.create(
            module_group=module_group,
            gbif_config=config,
            enabled=True,
            period=PublishPeriod.MONTHLY,
            run_at=timezone.datetime(2024, 1, 1, 2, 0).time(),
            day_of_month=None,
            timezone="UTC",
        )

        with schema_context(get_public_schema_name()):
            task = PeriodicTask.objects.get(
                name=f"GBIF publish: taxon_group={module_group.id} id={schedule.id}"
            )
            self.assertEqual(task.crontab.day_of_month, "1")
