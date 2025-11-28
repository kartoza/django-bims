import io
from contextlib import contextmanager, redirect_stdout
from decimal import Decimal
from unittest import mock

from django.core.management import call_command
from django_tenants.test.cases import FastTenantTestCase

from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
)


class TestUpdateGbifCoordinateFields(FastTenantTestCase):
    """Tests for the update_gbif_coordinate_fields management command."""

    @mock.patch(
        "scripts.management.commands.update_gbif_coordinate_fields.requests.Session"
    )
    def test_command_updates_site_fields(self, mock_session_cls):
        site = LocationSiteF.create(
            coordinate_precision=None,
            coordinate_uncertainty_in_meters=None,
            harvested_from_gbif=False,
        )
        BiologicalCollectionRecordF.create(
            site=site,
            upstream_id="123",
            source_collection="gbif",
        )

        mock_response = mock.Mock()
        mock_response.raise_for_status = mock.Mock()
        mock_response.json.return_value = {
            "coordinatePrecision": 0.00001,
            "coordinateUncertaintyInMeters": 30,
        }

        mock_session = mock_session_cls.return_value
        mock_session.get.return_value = mock_response

        out = io.StringIO()
        with redirect_stdout(out):
            call_command("update_gbif_coordinate_fields", limit=1, print_updates=True)
        output = out.getvalue()

        site.refresh_from_db()
        self.assertEqual(site.coordinate_precision, Decimal("0.00001"))
        self.assertEqual(site.coordinate_uncertainty_in_meters, Decimal("30"))
        self.assertTrue(site.harvested_from_gbif)
        mock_session.get.assert_called_once_with(
            "https://api.gbif.org/v1/occurrence/123", timeout=15
        )
        self.assertIn("Updated sites:", output)
        self.assertIn(str(site.id), output)

    @mock.patch(
        "scripts.management.commands.update_gbif_coordinate_fields.requests.Session"
    )
    def test_command_dry_run_skips_saving(self, mock_session_cls):
        site = LocationSiteF.create(
            coordinate_precision=None,
            coordinate_uncertainty_in_meters=None,
            harvested_from_gbif=False,
        )
        BiologicalCollectionRecordF.create(
            site=site,
            upstream_id="456",
            source_collection="gbif",
        )

        mock_response = mock.Mock()
        mock_response.raise_for_status = mock.Mock()
        mock_response.json.return_value = {
            "coordinatePrecision": 0.1,
            "coordinateUncertaintyInMeters": 5,
        }
        mock_session = mock_session_cls.return_value
        mock_session.get.return_value = mock_response

        call_command("update_gbif_coordinate_fields", limit=1, dry_run=True)

        site.refresh_from_db()
        self.assertIsNone(site.coordinate_precision)
        self.assertIsNone(site.coordinate_uncertainty_in_meters)
        self.assertFalse(site.harvested_from_gbif)
        mock_session.get.assert_called_once()

    @mock.patch(
        "scripts.management.commands.update_gbif_coordinate_fields.schema_context"
    )
    @mock.patch(
        "scripts.management.commands.update_gbif_coordinate_fields.Command._process_schema"
    )
    def test_command_schema_argument_uses_schema_context(
        self, mock_process_schema, mock_schema_context
    ):
        mock_context = mock.Mock()
        mock_context.__enter__ = mock.Mock(return_value=None)
        mock_context.__exit__ = mock.Mock(return_value=None)
        mock_schema_context.return_value = mock_context
        mock_process_schema.return_value = None

        call_command(
            "update_gbif_coordinate_fields", schema=self.tenant.schema_name
        )

        mock_schema_context.assert_called_once_with(self.tenant.schema_name)
        mock_process_schema.assert_called_once_with(100, False, False, False)

    @mock.patch(
        "scripts.management.commands.update_gbif_coordinate_fields.get_tenant_model"
    )
    @mock.patch(
        "scripts.management.commands.update_gbif_coordinate_fields.Command._process_schema"
    )
    @mock.patch(
        "scripts.management.commands.update_gbif_coordinate_fields.schema_context"
    )
    def test_command_all_tenants_iterates_each_schema(
        self,
        mock_schema_context,
        mock_process_schema,
        mock_get_tenant_model,
    ):
        mock_process_schema.return_value = None

        captured_schemas = []

        @contextmanager
        def fake_schema(name):
            captured_schemas.append(name)
            yield

        mock_schema_context.side_effect = fake_schema

        mock_qs = mock.MagicMock()
        mock_qs.exclude.return_value = mock_qs
        mock_qs.values_list.return_value = ["tenant_one", "tenant_two"]
        mock_model = mock.MagicMock()
        mock_model.objects = mock_qs
        mock_get_tenant_model.return_value = mock_model

        call_command("update_gbif_coordinate_fields", all_tenants=True)

        self.assertEqual(captured_schemas, ["tenant_one", "tenant_two"])
        self.assertEqual(mock_process_schema.call_count, 2)
