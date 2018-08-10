# coding=utf-8
"""Test Views Locate."""

import os
from django.test import SimpleTestCase

from bims.views.locate import get_farm_ids, parse_locate_return

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')



class TestLocateView(SimpleTestCase):
    """Test Locate View."""

    def test_locate_view(self):
        farms = get_farm_ids('C0010000000000010000%')
        for farm_key in farms.keys():
            self.assertIn('C0010000000000010000', farm_key)
        self.assertEqual(len(farms), 4)

        farms = get_farm_ids('C0010000000000010000')
        for farm_key in farms.keys():
            self.assertIn('C0010000000000010000', farm_key)
        self.assertEqual(len(farms), 4)

    def test_parse_locate_returns(self):
        """Test parsing locate returns xml document."""
        wfs_document_path = os.path.join(
            test_data_directory, 'geoserver_farm_id.xml')
        self.assertTrue(os.path.exists(wfs_document_path))
        with open(wfs_document_path) as file:
            wfs_string = file.read()

        farms = parse_locate_return(wfs_string)
        self.assertEqual(len(farms), 4)
        for farm_value in farms.values():
            self.assertIsNone(farm_value)

        farms = parse_locate_return(wfs_string, with_envelope=True)
        self.assertEqual(len(farms), 4)
        for farm_value in farms.values():
            self.assertIsNotNone(farm_value)
