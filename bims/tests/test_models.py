# coding=utf-8
"""Tests for models."""
from django.test import TestCase
from django.contrib.gis.geos import LineString
from django.core.exceptions import ValidationError
from django.db.models import signals
from bims.tests.model_factories import (
    LocationTypeF,
    LocationSiteF,
    TaxonomyF,
    IUCNStatusF,
    SurveyF,
    EndemismF,
    FbisUUIDF,
)
from bims.models.iucn_status import iucn_status_pre_save_handler
from bims.utils.get_key import get_key
from bims.models.location_site import LocationSite

geocontext_url = get_key('GEOCONTEXT_URL')
geocontext_collection_key = get_key('GEOCONTEXT_COLLECTION_KEY')

skip_geocontext = (not geocontext_url or not geocontext_collection_key)

first_url = LocationSite.geocontext_url_format.format(
    geocontext_url=geocontext_url,
    longitude='27.0',
    latitude='-31.0',
    geocontext_collection_key=geocontext_collection_key,
)

second_url = LocationSite.geocontext_url_format.format(
    geocontext_url=geocontext_url,
    longitude='26.0',
    latitude='-30.0',
    geocontext_collection_key=geocontext_collection_key,
)

first_json_data = {"key1": "value1"}
second_json_data = {"key2": "value2"}


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code, reason=''):
            self.json_data = json_data
            self.status_code = status_code
            self.reason = reason

        def json(self):
            return self.json_data

    if args[0] == first_url:
        return MockResponse(
            first_json_data,
            200
        )
    elif args[0] == second_url:
        return MockResponse(
            second_json_data,
            200
        )


    return MockResponse(None, 404, 'Not found for %s' % args[0])


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

    def test_LocationSite_update_lat_lon_manually(self):
        location_site = LocationSiteF.create()
        new_data = {
            'latitude': -33.3,
            'longitude': 25,
        }
        location_site.__dict__.update(new_data)

        # check if updated
        for key, val in new_data.items():
            self.assertEqual(location_site.__dict__.get(key), val)


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
        model = TaxonomyF.create()

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
        model = TaxonomyF.create(
            iucn_status=iucn_status,
            scientific_name=u'custom scientific name',
            canonical_name=u'custom common name',
            author=u'custom author'
        )

        self.assertTrue(model.iucn_status.category == 'custom iucn status')
        self.assertTrue(model.scientific_name == 'custom scientific name')
        self.assertTrue(model.canonical_name == 'custom common name')
        self.assertTrue(model.author == 'custom author')

    def test_Taxon_update(self):
        """
        Tests taxon model update
        """
        model = TaxonomyF.create()
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
        model = TaxonomyF.create()
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


class TestEndemismCRUD(TestCase):
    """
    Tests endemism model.
    """
    ENDEMISM_DEFAULT_VALUE = 'endemism'

    def setUp(self):
        """
        Sets up before each test
        """
        self.endemism1 = EndemismF.create(
            name=self.ENDEMISM_DEFAULT_VALUE
        )
        pass

    def test_Survey_create(self):
        """
        Tests endemism creation
        """

        # check if pk exists
        self.assertTrue(self.endemism1.pk is not None)

        # check if name exists
        self.assertTrue(self.endemism1.name is not None)

    def test_Survey_read(self):
        """
        Survey endemism model read
        """
        self.assertTrue(
            self.endemism1.name == self.ENDEMISM_DEFAULT_VALUE)

    def test_Survey_update(self):
        """
        Tests survey model update
        """
        new_data = {
            'name': 'endemism new value'
        }
        self.endemism1.__dict__.update(new_data)
        self.endemism1.save()

        # check if updated
        for key, val in new_data.items():
            self.assertEqual(self.endemism1.__dict__.get(key), val)

    def test_Survey_delete(self):
        """
        Tests survey model delete
        """
        model = EndemismF.create()
        model.delete()

        # check if deleted
        self.assertTrue(model.pk is None)


class TestFbisUUID(TestCase):
    """
    Tests FbisUUID model.
    """

    def setUp(self):
        """
        Sets up before each test
        """
        pass

    def test_create(self):
        """
        Tests FbisUUID creation
        """
        from django.contrib.contenttypes.models import ContentType
        from bims.models.endemism import Endemism

        endemism = EndemismF.create(name='test')
        ctype = ContentType.objects.get_for_model(Endemism)
        fbis_uuid = FbisUUIDF.create(
            content_type=ctype,
            object_id=endemism.id
        )
        self.assertEqual(fbis_uuid.content_object.id, endemism.id)
