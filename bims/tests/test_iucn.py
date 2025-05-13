import json
from unittest.mock import patch, Mock
from django_tenants.test.cases import FastTenantTestCase
from preferences import preferences

from bims.enums import TaxonomicRank
from bims.models.site_setting import SiteSetting
from bims.models.iucn_status import IUCNStatus
from bims.utils.iucn import get_iucn_status
from bims.tests.model_factories import TaxonomyF


class GetIUCNStatusTest(FastTenantTestCase):
    def setUp(self):
        genus = TaxonomyF.create(
            canonical_name="Galaxias",
            rank=TaxonomicRank.GENUS.name
        )
        self.taxon = TaxonomyF.create(
            canonical_name="Galaxias zebratus",
            rank=TaxonomicRank.SPECIES.name,
            parent=genus
        )
        site_setting = preferences.SiteSetting

        if not site_setting:
            site_setting = SiteSetting.objects.create()

        if site_setting:
            site_setting.iucn_api_key = 'token'
            site_setting.save()

    @patch("bims.utils.iucn.requests.get")
    def test_get_iucn_status_success(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "taxon": {"sis_id": 8816},
            "assessments": [
                {
                    "latest": True,
                    "red_list_category_code": "DD",
                    "url": "https://www.iucnredlist.org/species/8816/12934076"
                }
            ]
        }
        mock_get.return_value = mock_response

        status, sis_id, url = get_iucn_status(self.taxon)

        self.assertIsNotNone(status)
        self.assertEqual(status.category, "DD")
        self.assertEqual(sis_id, 8816)
        self.assertEqual(url, "https://www.iucnredlist.org/species/8816/12934076")
        self.assertTrue(IUCNStatus.objects.filter(category="DD").exists())

    @patch("bims.utils.iucn.requests.get")
    def test_get_iucn_status_not_found(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "taxon": {},
            "assessments": []
        }
        mock_get.return_value = mock_response

        status, sis_id, url = get_iucn_status(self.taxon)
        self.assertIsNone(status)
        self.assertIsNone(sis_id)
        self.assertIsNone(url)
