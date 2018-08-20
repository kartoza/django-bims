# coding=utf-8
"""Test Views Locate."""

import os
from django.test import SimpleTestCase

from bims.views.locate import (
    filter_farm_ids, parse_farm_ids, get_farm, parse_farm)

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
            test_data_directory, 'geoserver_farm_ids.xml')
        self.assertTrue(os.path.exists(wfs_document_path))
        with open(wfs_document_path) as file:
            wfs_string = file.read()

        farm_ids = parse_farm_ids(wfs_string)
        self.assertEqual(len(farm_ids), 4)
        for farm_id in farm_ids:
            self.assertIsNotNone(farm_id)

    def test_get_farm(self):
        """Test get_farm"""
        farm_id = 'C00100000000000100001'
        farm = get_farm(farm_id)
        self.assertEqual(farm['farm_id'], farm_id)
        expected_envelope_extent = (-32.22, 23.7354, -32.1787, 23.7978)
        self.assertEqual(farm['envelope_extent'], expected_envelope_extent)

    def test_parse_farm(self):
        """Test parse_farm"""
        farm_id = 'C00100000000000100001'
        wfs_document_path = os.path.join(
            test_data_directory, 'geoserver_farm.xml')
        self.assertTrue(os.path.exists(wfs_document_path))
        with open(wfs_document_path) as file:
            wfs_string = file.read()

        farm = parse_farm(wfs_string)
        self.assertEqual(farm['farm_id'], farm_id)
        expected_envelope_extent = (-32.22, 23.7354, -32.1787, 23.7978)
        self.assertEqual(farm['envelope_extent'], expected_envelope_extent)
