# coding=utf-8
"""Test Views Locate."""

import os
from django.test import SimpleTestCase

from bims.views.locate import filter_farm_ids, parse_farm_ids

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


class TestLocateView(SimpleTestCase):
    """Test Locate View."""

    def test_filter_farm_ids(self):
        """Test filter_farm_ids"""
        # With %
        farm_ids = filter_farm_ids('C0010000000000010000%')
        for farm_id in farm_ids:
            self.assertIn('C0010000000000010000', farm_id)
        self.assertEqual(len(farm_ids), 4)

        # Without %
        farm_ids = filter_farm_ids('C0010000000000010000')
        for farm_id in farm_ids:
            self.assertIn('C0010000000000010000', farm_id)
        self.assertEqual(len(farm_ids), 4)

    def test_parse_farm_ids(self):
        """Test parsing locate returns xml document."""
        wfs_document_path = os.path.join(
            test_data_directory, 'geoserver_farm_id.xml')
        self.assertTrue(os.path.exists(wfs_document_path))
        with open(wfs_document_path) as file:
            wfs_string = file.read()

        farm_ids = parse_farm_ids(wfs_string)
        self.assertEqual(len(farm_ids), 4)
        for farm_id in farm_ids:
            self.assertIsNotNone(farm_id)
