import json
from unittest.mock import patch, Mock
from django_tenants.test.cases import FastTenantTestCase
from preferences import preferences

from bims.enums import TaxonomicRank
from bims.models.site_setting import SiteSetting
from bims.models.iucn_status import IUCNStatus
from bims.utils.iucn import get_iucn_status
from bims.tasks.taxa import fetch_iucn_status
from bims.models import IUCNAssessment
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


class FetchIUCNStatusTaskTest(FastTenantTestCase):
    def setUp(self):
        genus = TaxonomyF.create(
            canonical_name="Testus",
            rank=TaxonomicRank.GENUS.name
        )
        self.taxon = TaxonomyF.create(
            canonical_name="Testus example",
            rank=TaxonomicRank.SPECIES.name,
            parent=genus,
            iucn_status=None
        )

    @patch("bims.utils.iucn.get_iucn_assessments")
    @patch("bims.utils.iucn.get_iucn_status")
    def test_fetch_iucn_status_creates_and_updates_assessments(
        self, mock_get_status, mock_get_assessments
    ):
        status_obj = IUCNStatus.objects.create(category="VU", national=False)
        mock_get_status.return_value = (
            status_obj, 219, "https://www.iucnredlist.org/species/219/1"
        )

        mock_get_assessments.side_effect = [
            ([
                {
                    "assessment_id": 100,
                    "year_published": "2022",
                    "latest": True,
                    "red_list_category_code": "V",
                    "url": "https://www.iucnredlist.org/species/219/100",
                    "scopes": [{"code": "1", "description": {"en": "Global"}}],
                    "sis_taxon_id": 219
                },
                {
                    "assessment_id": 101,
                    "year_published": "2020",
                    "latest": False,
                    "red_list_category_code": "EN",
                    "url": "https://www.iucnredlist.org/species/219/101",
                    "scopes": [{"code": "1", "description": {"en": "Global"}}],
                    "sis_taxon_id": 219
                },
            ], 219),
            ([
                {
                    "assessment_id": 100,
                    "year_published": "2022",
                    "latest": False,
                    "red_list_category_code": "EN",
                    "url": "https://www.iucnredlist.org/species/219/100-updated",
                    "scopes": [{"code": "1", "description": {"en": "Global"}}],
                    "sis_taxon_id": 219
                },
            ], 219),
        ]

        fetch_iucn_status(taxa_ids=[self.taxon.id])

        self.taxon.refresh_from_db()
        self.assertEqual(self.taxon.iucn_status.category, "VU")
        self.assertEqual(self.taxon.iucn_redlist_id, 219)
        self.assertIn(
            "https://www.iucnredlist.org/species/219/1",
            self.taxon.iucn_data
        )

        assessments = IUCNAssessment.objects.filter(taxonomy=self.taxon)
        self.assertEqual(assessments.count(), 2)

        assessment = IUCNAssessment.objects.get(
            taxonomy=self.taxon, assessment_id=100
        )
        self.assertEqual(assessment.year_published, 2022)
        self.assertEqual(assessment.red_list_category_code, "V")
        self.assertEqual(assessment.normalized_status.category, "VU")

        fetch_iucn_status(taxa_ids=[self.taxon.id])

        assessment.refresh_from_db()
        self.assertFalse(assessment.latest)
        self.assertEqual(assessment.red_list_category_code, "EN")
        self.assertEqual(
            assessment.url,
            "https://www.iucnredlist.org/species/219/100-updated"
        )
