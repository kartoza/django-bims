# coding=utf-8
"""Tests for models."""
import json
import requests
import unittest
from django.test import TestCase
from django.contrib.gis.geos import LineString, Point
from django.core.exceptions import ValidationError
from django.db.models import signals
from bims.tests.model_factories import (
    LocationTypeF,
    LocationSiteF,
    TaxonF,
    IUCNStatusF,
    SurveyF,
)
from bims.models.iucn_status import iucn_status_pre_save_handler
from bims.utils.get_key import get_key

skip_geocontext = (
        not get_key('GEOCONTEXT_URL') or
        not get_key('GEOCONTEXT_COLLECTION_KEY'))
if not skip_geocontext:
    if requests.get(get_key('GEOCONTEXT_URL')).status_code != 200:
        skip_geocontext = True


class TestLocationTypeCRUD(TestCase):
    """
    Tests location type.
    """
    def setUp(self):
        """
        Sets up before each test
        """
        pass

    def test_LocationType_create(self):
        """
        Tests location type creation
        """
        model = LocationTypeF.create()

        # check if pk exists
        self.assertTrue(model.pk is not None)

        # check if name exists
        self.assertTrue(model.name is not None)

        # check if description exists
        self.assertTrue(model.description is not None)

    def test_LocationType_read(self):
        """
        Tests location type model read
        """
        model = LocationTypeF.create(
            name=u'custom location',
            description=u'custom description',
        )

        self.assertTrue(model.name == 'custom location')
        self.assertTrue(model.description == 'custom description')

    def test_LocationType_update(self):
        """
        Tests location type model update
        """
        model = LocationTypeF.create()
        new_data = {
            'name': u'new name',
            'description': u'new description'
        }
        model.__dict__.update(new_data)
        model.save()

        # check if updated
        for key, val in new_data.items():
            self.assertEqual(model.__dict__.get(key), val)

    def test_LocationType_delete(self):
        """
        Tests location type model delete
        """
        model = LocationTypeF.create()
        model.delete()

        # check if deleted
        self.assertTrue(model.pk is None)


class TestLocationSiteCRUD(TestCase):
    """
    Tests location site.
    """
    def setUp(self):
        """
        Sets up before each test
        """
        pass

    def test_LocationSite_create(self):
        """
        Tests location site creation
        """
        model = LocationSiteF.create()

        # check if pk exists
        self.assertTrue(model.pk is not None)

        # check if location_type exists
        self.assertTrue(model.location_type is not None)

        # check if geometry exists
        self.assertTrue(model.geometry_point is not None)

    def test_LocationSite_read(self):
        """
        Tests location site model read
        """
        location_type = LocationTypeF.create(
            name=u'custom type',
        )
        model = LocationSiteF.create(
            location_type=location_type
        )

        try:
            location_context = json.loads(
                    model.location_context.context_document
            )
            self.assertTrue(len(location_context['features']) > 0)
        except ValueError:
            pass

        self.assertTrue(model.location_type.name == 'custom type')

    def test_LocationSite_update(self):
        """
        Tests location site model update
        """
        location_type = LocationTypeF.create(
                name=u'custom type',
        )
        model = LocationSiteF.create()
        new_data = {
            'location_type': location_type,
        }
        model.__dict__.update(new_data)
        model.save()

        # check if updated
        for key, val in new_data.items():
            self.assertEqual(model.__dict__.get(key), val)

    def test_LocationSite_delete(self):
        """
        Tests location site model delete
        """
        model = LocationSiteF.create()
        model.delete()

        # check if deleted
        self.assertTrue(model.pk is None)

    def test_LocationSite_update_not_in_allowed_geometry(self):
        """
        Tests location site model update if geometry is not in allowed
        geometry
        """
        location_site = LocationSiteF.create()
        new_data = {
            'geometry_point': None,
            'geometry_line': LineString((1, 1), (2, 2)),
        }
        location_site.__dict__.update(new_data)

        # check if validation error raised
        self.assertRaises(ValidationError, location_site.save)

    @unittest.skipIf(
        skip_geocontext,
        'Either geocontext url or collection key is not found or the '
        'geocontext url is not accessible.')
    def test_LocationSite_update_location_context_document(self):
        """Test updating location context document"""
        location_site = LocationSiteF.create()
        new_point = {
            'geometry_point': Point(27, -31),
        }
        location_site.__dict__.update(new_point)
        location_site.save()
        self.assertIsNone(location_site.location_context_document)
        status, message = location_site.update_location_context_document()
        self.assertTrue(status, message)
        self.assertIsNotNone(location_site.location_context_document)


class TestIUCNStatusCRUD(TestCase):
    """
       Tests iucn status.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        pass

    def test_IUCNStatus_create(self):
        """
        Tests iucn status creation
        """
        model = IUCNStatusF.create()

        # check if pk exists
        self.assertTrue(model.pk is not None)

        # check if name exists
        self.assertTrue(model.category is not None)

    def test_IUCNStatus_read(self):
        """
        Tests iucn status model read
        """
        model = IUCNStatusF.create(
            category=u'custom iucn status',
            sensitive=False,
        )

        self.assertTrue(model.category == 'custom iucn status')
        self.assertFalse(model.sensitive)

    def test_IUCNStatus_update(self):
        """
        Tests iucn status model update
        """
        model = IUCNStatusF.create()
        new_data = {
            'category': u'new name',
            'sensitive': False,
        }
        model.__dict__.update(new_data)
        model.save()

        # check if updated
        for key, val in new_data.items():
            self.assertEqual(model.__dict__.get(key), val)

    def test_IUCNStatus_delete(self):
        """
        Tests iucn status model delete
        """
        model = IUCNStatusF.create()
        model.delete()

        # check if deleted
        self.assertTrue(model.pk is None)

    def test_signal_registry(self):
        """
        Test signal is registered.
        """
        registered_signal = [r[1]() for r in signals.pre_save.receivers]
        self.assertIn(iucn_status_pre_save_handler, registered_signal)


class TestTaxonCRUD(TestCase):
    """
    Tests taxon.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        pass

    def test_Taxon_create(self):
        """
        Tests taxon creation
        """
        model = TaxonF.create()

        # check if pk exists
        self.assertTrue(model.pk is not None)

        # check if iucn_status exists
        self.assertTrue(model.iucn_status is not None)

        # check if scientific name exists
        self.assertTrue(model.scientific_name is not None)

    def test_Taxon_read(self):
        """
        Tests taxon model read
        """
        iucn_status = IUCNStatusF.create(
            category=u'custom iucn status',
            sensitive=True,
        )
        model = TaxonF.create(
            iucn_status=iucn_status,
            scientific_name=u'custom scientific name',
            common_name=u'custom common name',
            author=u'custom author'
        )

        self.assertTrue(model.iucn_status.category == 'custom iucn status')
        self.assertTrue(model.scientific_name == 'custom scientific name')
        self.assertTrue(model.common_name == 'custom common name')
        self.assertTrue(model.author == 'custom author')

    def test_Taxon_update(self):
        """
        Tests taxon model update
        """
        model = TaxonF.create()
        iucn_status = IUCNStatusF.create(
            category=u'custom iucn status',
            sensitive=True,
        )
        new_data = {
            'iucn_status': iucn_status,
            'scientific_name': u'new scientific name',
            'common_name': u'new common name',
            'author': u'custom author',
        }
        model.__dict__.update(new_data)
        model.save()

        # check if updated
        for key, val in new_data.items():
            self.assertEqual(model.__dict__.get(key), val)

    def test_Taxon_delete(self):
        """
        Tests taxon model delete
        """
        model = TaxonF.create()
        model.delete()

        # check if deleted
        self.assertTrue(model.pk is None)


class TestSurveyCRUD(TestCase):
    """
    Tests survey.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        self.location_site_1 = LocationSiteF.create(
            pk=1
        )
        self.location_site_2 = LocationSiteF.create(
            pk=2
        )
        pass

    def test_Survey_create(self):
        """
        Tests taxon creation
        """
        model = SurveyF.create(
                sites=(self.location_site_1, self.location_site_2)
        )

        # check if pk exists
        self.assertTrue(model.pk is not None)

        # check if date exists
        self.assertTrue(model.date is not None)

        # check if sites name exists
        self.assertTrue(model.sites is not None)

    def test_Survey_read(self):
        """
        Survey taxon model read
        """
        survey = SurveyF.create(
            sites=(self.location_site_1, self.location_site_2)
        )

        self.assertTrue(survey.sites.get(pk=1) == self.location_site_1)

    def test_Survey_update(self):
        """
        Tests survey model update
        """
        model = SurveyF.create()
        new_data = {
            'sites': (self.location_site_1, self.location_site_2),
        }
        model.__dict__.update(new_data)
        model.save()

        # check if updated
        for key, val in new_data.items():
            self.assertEqual(model.__dict__.get(key), val)

    def test_Survey_delete(self):
        """
        Tests survey model delete
        """
        model = SurveyF.create()
        model.delete()

        # check if deleted
        self.assertTrue(model.pk is None)
