from django.test import TestCase
from django.contrib.gis.geos import Point
from rest_framework.test import APIRequestFactory
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
)
from bims.tests.model_factories import (
    LocationSiteF,
    TaxonF,
)
from bims.api_views.cluster_collection_by_taxon import (
    ClusterCollectionByTaxon
)


class TestApiView(TestCase):
    """Test clustering collection by taxon API """
    url = '/api/cluster/collection/taxon/%(taxon_id)s?' \
          'icon_pixel_x=30&icon_pixel_y=30&' \
          'zoom=%(zoom)s&bbox=0.0,0.0,25.0,25.0'
    url_bbox_shrinked = '/api/cluster/collection/taxon/%(taxon_id)s?' \
                        'icon_pixel_x=30&icon_pixel_y=30&' \
                        'zoom=%(zoom)s&bbox=20.0,20.0,25.0,25.0'

    def setUp(self):
        self.factory = APIRequestFactory()
        self.taxon_1 = TaxonF.create(
            pk=1,
            common_name=u'Test fish',
        )
        self.location_site_1 = LocationSiteF.create(
            geometry_point=Point(10, 10)
        )
        self.location_site_2 = LocationSiteF.create(
            geometry_point=Point(20, 20)
        )
        self.fish_collection_1 = BiologicalCollectionRecordF.create(
            original_species_name='fish 1',
            taxon_gbif_id=self.taxon_1,
            site=self.location_site_1
        )
        self.fish_collection_2 = BiologicalCollectionRecordF.create(
            original_species_name='fish 2',
            taxon_gbif_id=self.taxon_1,
            site=self.location_site_2
        )
        self.taxon_2 = TaxonF.create(
            pk=2,
            common_name=u'Test fish 2',
        )
        self.fish_collection_3 = BiologicalCollectionRecordF.create(
            original_species_name='fish 3',
            taxon_gbif_id=self.taxon_2,
            site=self.location_site_1
        )

    def test_get_cluster_taxon_1_zoom_1(self):
        view = ClusterCollectionByTaxon.as_view()
        request = self.factory.get(
            self.url % {
                'taxon_id': 1,
                'zoom': 1
            })
        response = view(request, 1)
        features = response.data
        self.assertEqual(
            len(features), 1)
        self.assertEqual(
            features[0]['properties']['count'], 2)

    def test_get_cluster_taxon_1_zoom_1_bbox_shrinked(self):
        view = ClusterCollectionByTaxon.as_view()
        request = self.factory.get(
            self.url_bbox_shrinked % {
                'taxon_id': 1,
                'zoom': 1
            })
        response = view(request, 1)
        features = response.data
        self.assertEqual(
            len(features), 1)
        self.assertEqual(
            features[0]['properties']['taxon_gbif_id'], 1)
        self.assertEqual(
            features[0]['properties']['original_species_name'],
            self.fish_collection_2.original_species_name)

    def test_get_cluster_taxon_1_zoom_18(self):
        view = ClusterCollectionByTaxon.as_view()
        request = self.factory.get(
            self.url % {
                'taxon_id': 1,
                'zoom': 18
            })
        response = view(request, 1)
        features = response.data
        self.assertEqual(
            len(features), 2)
        for feature in features:
            self.assertEqual(
                feature['properties']['taxon_gbif_id'], 1)

    def test_get_cluster_taxon_2_zoom_18(self):
        view = ClusterCollectionByTaxon.as_view()
        request = self.factory.get(
            self.url % {
                'taxon_id': 2,
                'zoom': 18
            })
        response = view(request, 2)
        features = response.data
        self.assertEqual(
            len(features), 1)
        for feature in features:
            self.assertEqual(
                feature['properties']['taxon_gbif_id'], 2)

    def test_get_cluster_taxon_2_zoom_18_bbox_shrinked(self):
        view = ClusterCollectionByTaxon.as_view()
        request = self.factory.get(
            self.url_bbox_shrinked % {
                'taxon_id': 2,
                'zoom': 18
            })
        response = view(request, 2)
        features = response.data
        self.assertEqual(
            len(features), 0)
