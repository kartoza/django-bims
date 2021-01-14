import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from bims.api_views.remove_occurrences import RemoveOccurrencesApiView
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    UserF,
    LocationSiteF,
    TaxonomyF,
    LocationContextF,
    TaxonGroupF,
    VernacularNameF,
    SurveyF
)
from bims.models import (
    BiologicalCollectionRecord,
    Taxonomy,
    Survey,
    LocationSite,
    SiteSetting,
    TaxonGroup
)



class TestRemoveOccurrencesApi(TestCase):
    """Test Remove Occurrences Api"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_remove_data(self):
        site_setting, _ = SiteSetting.objects.get_or_create()
        site_setting.enable_remove_all_occurrences_tool = True
        site_setting.save()

        vernacular_name_1 = VernacularNameF.create()
        taxonomy_1 = TaxonomyF.create(
            id=1,
            vernacular_names=[vernacular_name_1])
        taxonomy_2 = TaxonomyF.create(id=2)
        taxonomy_3 = TaxonomyF.create(id=3)
        view = RemoveOccurrencesApiView.as_view()

        taxon_group_1 = TaxonGroupF.create(
            id=1,
            taxonomies=(taxonomy_1,
                        taxonomy_2,
                        taxonomy_3)
        )
        site_1 = LocationSiteF.create()
        site_2 = LocationSiteF.create()
        LocationContextF.create(site=site_1)
        LocationContextF.create(site=site_2)

        BiologicalCollectionRecordF.create(
            site=site_1,
            taxonomy=taxonomy_3
        )

        bio_1 = BiologicalCollectionRecordF.create(
            module_group=taxon_group_1,
            site=site_1,
            taxonomy=taxonomy_1,
            survey=SurveyF.create(site=site_1)
        )
        bio_2 = BiologicalCollectionRecordF.create(
            module_group=taxon_group_1,
            site=site_2,
            taxonomy=taxonomy_1,
            survey=SurveyF.create(site=site_2)
        )
        surveys = Survey.objects.filter(
            biological_collection_record__in=[bio_1, bio_2]
        )
        survey_ids = list(surveys.values_list('id', flat=True))
        site_ids = [site_1.id, site_2.id]

        request = self.factory.get(
            reverse('remove-occurrences') + '?taxon_module=1'
        )

        self.assertTrue(
            LocationSite.objects.filter(id__in=site_ids).exists()
        )

        user = UserF.create(
            is_superuser=True
        )
        request.user = user
        response = view(request)
        content = json.loads(response.content)

        self.assertEqual(content['Collections deleted'], 2)
        self.assertEqual(content['Taxa deleted'], 3)
        self.assertEqual(content['Survey deleted'], 2)
        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(
                module_group_id=taxon_group_1.id
            ).exists()
        )
        self.assertFalse(
            Taxonomy.objects.filter(id__in=[1, 2]).exists()
        )
        self.assertFalse(
            Survey.objects.filter(id__in=survey_ids).count() > 0
        )
        self.assertFalse(
            LocationSite.objects.filter(id__in=site_ids).count() > 1
        )
        self.assertFalse(
            TaxonGroup.objects.filter(id=1).exists()
        )
