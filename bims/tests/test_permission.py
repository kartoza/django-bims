# coding=utf-8
"""Tests for permissions."""

from django.test import TestCase
from bims.tests.model_factories import (
    PermissionF,
    TaxonomyF,
)
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.permissions.generate_permission import generate_permission


class TestValidatorPermission(TestCase):
    """ Tests permission for validator.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        self.taxon = TaxonomyF.create(
            scientific_name='Aves',
            rank=TaxonomicRank.CLASS.name
        )
        self.permission = PermissionF.create(
            name='Can validate data',
            codename='can_validate_data'
        )

    def test_permission_generated(self):
        """
        Tests if permission generated if there is new taxon class
        """
        taxon_class = 'Animalia'
        result = generate_permission(taxon_class)
        self.assertIsNotNone(result)

    def test_permission_already_exists(self):
        """
        Tests existed permission not generated
        """
        taxon_class = 'Aves'
        result = generate_permission(taxon_class)
        self.assertIsNone(result)
