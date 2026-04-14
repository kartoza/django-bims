"""
Tests for the FIPS site-code generator (bims.utils.site_code.fips_generator).

Each test patches ``bims.utils.site_code.get_feature_data`` so that no real
GIS database or cloud_native_gis Layer objects are required.  The settings
that control which layer/field names are used are patched on the ``bims.conf``
module directly so every combination can be exercised in isolation.
"""

from unittest.mock import patch, call

from django.test import TestCase, override_settings

from bims.utils.site_code import fips_generator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_feature_data_side_effect(**mapping):
    """
    Return a side-effect function for ``get_feature_data`` that returns a
    pre-defined value based on the ``layer_name`` kwarg.

    ``mapping`` should be  {layer_name: return_value, ...}.
    Any layer not in the mapping returns ``''``.
    """
    def _side_effect(lon, lat, context_key, layer_name, tolerance=0, location_site=None):
        return mapping.get(layer_name, '')
    return _side_effect


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class FipsGeneratorContinentOnlyTest(TestCase):
    """Continent layer present, basin/subbasin/hydrobasin all disabled."""

    @patch('bims.conf.FIPS_BASIN_LAYER', '')
    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.utils.site_code.get_feature_data')
    def test_returns_continent_code_only(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(continent='AF')

        result = fips_generator(lat=-1.0, lon=30.0)

        self.assertEqual(result, 'AF')

    @patch('bims.conf.FIPS_BASIN_LAYER', '')
    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.utils.site_code.get_feature_data')
    def test_continent_not_found_returns_xx(self, mock_gfd):
        """When continent layer returns nothing, the fallback is 'XX'."""
        mock_gfd.return_value = ''

        result = fips_generator(lat=0.0, lon=0.0)

        self.assertEqual(result, 'XX')

    @patch('bims.conf.FIPS_BASIN_LAYER', '')
    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.utils.site_code.get_feature_data')
    def test_continent_code_stripped_to_two_alpha_chars(self, mock_gfd):
        """Non-alpha characters are removed and value is capped at 2 chars."""
        mock_gfd.side_effect = _make_feature_data_side_effect(continent='1EU-extra')

        result = fips_generator(lat=48.0, lon=2.0)

        # '1EU-extra' → strip non-alpha → 'EUextra' → [:2] → 'EU'
        self.assertEqual(result, 'EU')


class FipsGeneratorContinentAndBasinTest(TestCase):
    """Default config: continent + basin, no subbasin or hydrobasin."""

    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.utils.site_code.get_feature_data')
    def test_continent_and_basin_concatenated(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='AF',
            basin='Atlantic Ocean',
        )

        result = fips_generator(lat=-1.0, lon=10.0)

        # basin: 'Atlantic Ocean' → strip non-alnum → 'AtlanticOcean' → [:3] → 'ATL'
        self.assertEqual(result, 'AFATL')

    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.utils.site_code.get_feature_data')
    def test_basin_not_found_omitted_gracefully(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(continent='AS')

        result = fips_generator(lat=20.0, lon=80.0)

        self.assertEqual(result, 'AS')

    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.utils.site_code.get_feature_data')
    def test_basin_name_with_special_chars_cleaned(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='EU',
            basin='Rhine-Meuse & Alps',
        )

        result = fips_generator(lat=51.0, lon=6.0)

        # 'Rhine-Meuse & Alps' → strip non-alnum → 'RhineMeuseAlps' → [:3].upper() → 'RHI'
        # prefix = 'EU' + 'RHI' = 'EURHI'
        self.assertEqual(result, 'EURHI')


class FipsGeneratorWithSubbasinTest(TestCase):
    """Subbasin layer configured."""

    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.conf.FIPS_SUBBASIN_LAYER', 'subbasin')
    @patch('bims.conf.FIPS_SUBBASIN_FIELD', 'name')
    @patch('bims.utils.site_code.get_feature_data')
    def test_subbasin_appended_to_prefix(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='AF',
            basin='Congo',
            subbasin='Lualaba',
        )

        result = fips_generator(lat=-5.0, lon=27.0)

        # continent=AF, basin=Congo→CON, subbasin=Lualaba→LUA
        self.assertEqual(result, 'AFCONLUA')

    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.conf.FIPS_SUBBASIN_LAYER', 'subbasin')
    @patch('bims.conf.FIPS_SUBBASIN_FIELD', 'name')
    @patch('bims.utils.site_code.get_feature_data')
    def test_subbasin_not_found_omitted(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='AF',
            basin='Congo',
            # subbasin returns ''
        )

        result = fips_generator(lat=-5.0, lon=27.0)

        self.assertEqual(result, 'AFCON')

    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.conf.FIPS_SUBBASIN_LAYER', 'subbasin')
    @patch('bims.conf.FIPS_SUBBASIN_FIELD', 'name')
    @patch('bims.utils.site_code.get_feature_data')
    def test_subbasin_capped_at_three_chars(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='AF',
            basin='Congo',
            subbasin='Lualaba River Upper',
        )

        result = fips_generator(lat=-5.0, lon=27.0)

        # subbasin → 'LualabaRiverUpper' stripped → [:3] → 'LUA'
        self.assertEqual(result, 'AFCONLUA')


class FipsGeneratorWithHydrobasinTest(TestCase):
    """HydroBASIN layer configured."""

    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', 'hydrobasin')
    @patch('bims.conf.FIPS_HYDROBASIN_FIELD', 'HYBAS_ID')
    @patch('bims.utils.site_code.get_feature_data')
    def test_hydrobasin_id_appended(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='AF',
            basin='Congo',
            hydrobasin='4040000010',
        )

        result = fips_generator(lat=-5.0, lon=27.0)

        self.assertEqual(result, 'AFCON4040000010')

    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', 'hydrobasin')
    @patch('bims.conf.FIPS_HYDROBASIN_FIELD', 'HYBAS_ID')
    @patch('bims.utils.site_code.get_feature_data')
    def test_hydrobasin_not_found_omitted(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='AF',
            basin='Congo',
            # hydrobasin returns ''
        )

        result = fips_generator(lat=-5.0, lon=27.0)

        self.assertEqual(result, 'AFCON')

    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', '')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', 'hydrobasin')
    @patch('bims.conf.FIPS_HYDROBASIN_FIELD', 'HYBAS_ID')
    @patch('bims.utils.site_code.get_feature_data')
    def test_hydrobasin_without_basin(self, mock_gfd):
        """HydroBASIN can be used even when basin layer is disabled."""
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='EU',
            hydrobasin='2050012345',
        )

        result = fips_generator(lat=48.0, lon=2.0)

        self.assertEqual(result, 'EU2050012345')


class FipsGeneratorAllLayersTest(TestCase):
    """All four layers configured and returning data."""

    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.conf.FIPS_SUBBASIN_LAYER', 'subbasin')
    @patch('bims.conf.FIPS_SUBBASIN_FIELD', 'name')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', 'hydrobasin')
    @patch('bims.conf.FIPS_HYDROBASIN_FIELD', 'HYBAS_ID')
    @patch('bims.utils.site_code.get_feature_data')
    def test_all_layers_combined(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='AF',
            basin='Congo',
            subbasin='Lualaba',
            hydrobasin='4040000010',
        )

        result = fips_generator(lat=-5.0, lon=27.0)

        # basin=Congo→CON, subbasin=Lualaba→LUA
        self.assertEqual(result, 'AFCONLUA4040000010')

    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.conf.FIPS_SUBBASIN_LAYER', 'subbasin')
    @patch('bims.conf.FIPS_SUBBASIN_FIELD', 'name')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', 'hydrobasin')
    @patch('bims.conf.FIPS_HYDROBASIN_FIELD', 'HYBAS_ID')
    @patch('bims.utils.site_code.get_feature_data')
    def test_all_layers_none_found_returns_xx(self, mock_gfd):
        """Even with all layers configured, missing data returns minimal code."""
        mock_gfd.return_value = ''

        result = fips_generator(lat=0.0, lon=0.0)

        self.assertEqual(result, 'XX')

    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'continent')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'cont_code')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'basin')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'WMOBB_NAME')
    @patch('bims.conf.FIPS_SUBBASIN_LAYER', 'subbasin')
    @patch('bims.conf.FIPS_SUBBASIN_FIELD', 'name')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', 'hydrobasin')
    @patch('bims.conf.FIPS_HYDROBASIN_FIELD', 'HYBAS_ID')
    @patch('bims.utils.site_code.get_feature_data')
    def test_correct_layer_names_and_fields_passed(self, mock_gfd):
        """Verify that each layer query uses the configured layer_name and context_key."""
        mock_gfd.side_effect = _make_feature_data_side_effect(
            continent='AF',
            basin='Congo',
            subbasin='Lualaba',
            hydrobasin='4040000010',
        )

        fips_generator(lat=-5.0, lon=27.0)

        calls = mock_gfd.call_args_list
        layer_names_queried = [c.kwargs.get('layer_name') or c.args[3] for c in calls]
        context_keys_queried = [c.kwargs.get('context_key') or c.args[2] for c in calls]

        self.assertIn('continent', layer_names_queried)
        self.assertIn('basin', layer_names_queried)
        self.assertIn('subbasin', layer_names_queried)
        self.assertIn('hydrobasin', layer_names_queried)

        self.assertIn('cont_code', context_keys_queried)
        self.assertIn('WMOBB_NAME', context_keys_queried)
        self.assertIn('name', context_keys_queried)
        self.assertIn('HYBAS_ID', context_keys_queried)


class FipsGeneratorCustomSettingsTest(TestCase):
    """Verify that custom layer/field names from settings are honoured."""

    @patch('bims.conf.FIPS_SUBBASIN_LAYER', '')
    @patch('bims.conf.FIPS_HYDROBASIN_LAYER', '')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_LAYER', 'my_continent_layer')
    @patch('bims.conf.FIPS_GBIF_CONTINENT_FIELD', 'my_cont_field')
    @patch('bims.conf.FIPS_BASIN_LAYER', 'my_basin_layer')
    @patch('bims.conf.FIPS_BASIN_FIELD', 'my_basin_field')
    @patch('bims.utils.site_code.get_feature_data')
    def test_custom_layer_names_used(self, mock_gfd):
        mock_gfd.side_effect = _make_feature_data_side_effect(
            my_continent_layer='SA',
            my_basin_layer='Amazon',
        )

        result = fips_generator(lat=-10.0, lon=-60.0)

        # 'Amazon' → strip non-alnum → 'Amazon' → [:3].upper() → 'AMA'
        self.assertEqual(result, 'SAAMA')

        # Ensure custom layer names were passed to get_feature_data
        continent_call = next(
            c for c in mock_gfd.call_args_list
            if (c.kwargs.get('layer_name') or c.args[3]) == 'my_continent_layer'
        )
        self.assertEqual(
            continent_call.kwargs.get('context_key') or continent_call.args[2],
            'my_cont_field'
        )
