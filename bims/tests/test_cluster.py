# coding=utf-8
"""Tests for models."""

from django.test import TestCase
from bims.tests.model_factories import (
    BoundaryF,
    BoundaryTypeF,
    ClusterF
)


class TestBoundaryType(TestCase):
    """ Tests CURD cluster.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        pass

    def test_boundary_type_create(self):
        """
        Tests creation
        """
        boundary_type = BoundaryTypeF.create()

        # check if pk exists
        self.assertTrue(boundary_type.pk is not None)

    def test_boundary_type_read(self):
        """
        Tests read
        """
        boundary_type = BoundaryTypeF.create(
            name='country'
        )

        self.assertTrue(boundary_type.name == 'country')

    def test_boundary_type_update(self):
        """
        Tests boundary type update
        """
        boundary_type = BoundaryTypeF.create()
        boundary_type_data = {
            'name': 'province'
        }
        boundary_type.__dict__.update(boundary_type_data)
        boundary_type.save()

        # check if updated
        for key, val in boundary_type_data.items():
            self.assertEqual(getattr(boundary_type, key), val)

    def test_boundary_type_delete(self):
        """
        Tests boundary type model delete
        """
        boundary_type = BoundaryTypeF.create()
        boundary_type.delete()

        # check if deleted
        self.assertTrue(boundary_type.pk is None)


class TestBoundary(TestCase):
    """ Tests CURD cluster.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        pass

    def test_boundary_create(self):
        """
        Tests creation
        """
        boundary = BoundaryF.create()

        # check if pk exists
        self.assertTrue(boundary.pk is not None)

    def test_boundary_read(self):
        """
        Tests read
        """
        boundary_type = BoundaryTypeF.create(
            name='country'
        )
        boundary = BoundaryF.create(
            name='South Africa',
            type=boundary_type
        )

        self.assertTrue(boundary.name == 'South Africa')
        self.assertTrue(boundary.type.name == 'country')

    def test_boundary_update(self):
        """
        Tests boundary update
        """
        boundary_type = BoundaryTypeF.create(
            name='country'
        )
        boundary = BoundaryF.create()
        boundary_data = {
            'name': 'South Africa',
            'type': boundary_type
        }
        boundary.__dict__.update(boundary_data)
        boundary.type = boundary_type
        boundary.save()

        # check if updated
        for key, val in boundary_data.items():
            self.assertEqual(getattr(boundary, key), val)

    def test_boundary_delete(self):
        """
        Tests boundary model delete
        """
        boundary = BoundaryF.create()
        boundary.delete()

        # check if deleted
        self.assertTrue(boundary.pk is None)


class TestCluster(TestCase):
    """ Tests CURD cluster.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        pass

    def test_cluster_create(self):
        """
        Tests creation
        """
        cluster = ClusterF.create()

        # check if pk exists
        self.assertTrue(cluster.pk is not None)

    def test_cluster_read(self):
        """
        Tests read
        """
        boundary_type = BoundaryTypeF.create(
            name='country'
        )
        boundary = BoundaryF.create(
            name='South Africa',
            type=boundary_type
        )
        cluster = ClusterF.create(
            boundary=boundary,
            site_count=10,
            details='{}',
            module='fish'
        )

        self.assertTrue(cluster.boundary.name == 'South Africa')
        self.assertTrue(cluster.boundary.type.name == 'country')
        self.assertTrue(cluster.site_count == 10)
        self.assertTrue(cluster.module == 'fish')
        self.assertTrue(cluster.details == '{}')

    def test_cluster_update(self):
        """
        Tests cluster update
        """
        boundary_type = BoundaryTypeF.create(
            name='country'
        )
        boundary = BoundaryF.create(
            name='South Africa',
            type=boundary_type,
        )
        cluster_data = {
            'site_count': 1,
            'details': '{}',
            'module': 'rock',
            'boundary': boundary
        }
        cluster = ClusterF.create()
        cluster.__dict__.update(cluster_data)
        cluster.boundary = boundary
        cluster.save()

        # check if updated
        for key, val in cluster_data.items():
            self.assertEqual(getattr(cluster, key), val)

    def test_cluster_delete(self):
        """
        Tests cluster model delete
        """
        cluster = ClusterF.create()
        cluster.delete()

        # check if deleted
        self.assertTrue(cluster.pk is None)
