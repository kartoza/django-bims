import json
from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    UserF,
    ContentTypeF,
    PermissionF,
    GroupF,
    LocationSiteF,
    TaxonomyF,
    TaxonGroupF
)
from bims.api_views.location_site import (
    LocationSiteDetail,
)
from bims.api_views.location_type import (
    LocationTypeAllowedGeometryDetail
)
from bims.api_views.non_validated_record import (
    GetNonValidatedRecords
)
from bims.api_views.taxon import TaxonDetail
from bims.api_views.reference_category import ReferenceCategoryList
from bims.api_views.module_summary import ModuleSummary
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.views.autocomplete_search import autocomplete
from django.test import TestCase


class TestApiView(TestCase):
    """Test Location site API """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.location_site = LocationSiteF.create(
            pk=1,
            location_context_document='""'
        )

        self.taxonomy_class_1 = TaxonomyF.create(
            scientific_name='Aves',
            rank=TaxonomicRank.CLASS.name
        )
        self.taxonomy_1 = TaxonomyF.create(
            scientific_name='Some aves name 1',
            canonical_name='aves name 1',
            rank=TaxonomicRank.SPECIES.name,
            parent=self.taxonomy_class_1
        )
        self.taxonomy_2 = TaxonomyF.create(
            scientific_name='Some aves name 2',
            canonical_name='aves name 2',
            rank=TaxonomicRank.SPECIES.name,
            parent=self.taxonomy_class_1
        )
        self.aves_collection_1 = BiologicalCollectionRecordF.create(
            original_species_name=u'Aves collection 1',
            site=self.location_site,
            validated=True,
            ready_for_validation=True,
            taxonomy=self.taxonomy_1
        )
        self.aves_collection_2 = BiologicalCollectionRecordF.create(
            original_species_name=u'Aves collection 2',
            site=self.location_site,
            validated=True,
            ready_for_validation=True,
            taxonomy=self.taxonomy_2
        )

        self.fish_collection_1 = BiologicalCollectionRecordF.create(
            original_species_name=u'Test fish species name 1',
            site=self.location_site,
            validated=True
        )
        self.fish_collection_2 = BiologicalCollectionRecordF.create(
            original_species_name=u'Test fish species name 2',
            site=self.location_site,
            validated=True
        )
        self.admin_user = UserF.create(
            is_superuser=True,
            is_staff=True
        )

    def test_get_location_by_id(self):
        view = LocationSiteDetail.as_view()
        pk = '1'
        request = self.factory.get('/api/location-site-detail/?siteId=' + pk)
        response = view(request)
        self.assertTrue(
            'id' in response.data
        )

    def test_get_taxon_by_id(self):
        pk = 1
        taxon = TaxonomyF.create(
            pk=1,
            scientific_name=u'Golden fish',
        )
        view = TaxonDetail.as_view()
        request = self.factory.get('/api/taxon/' + str(pk))
        response = view(request, str(pk))
        self.assertEqual(
            taxon.scientific_name,
            response.data['scientific_name']
        )

        # def test_get_allowed_geometry_location_type_by_id(self):
        view = LocationTypeAllowedGeometryDetail.as_view()
        pk = '%s' % self.fish_collection_1.site.location_type.pk
        request = self.factory.get(
            '/api/location-type/%s/allowed-geometry/' % pk)
        response = view(request, pk)
        self.assertEqual(response.data, 'POINT')

    def test_get_unvalidated_records_as_public(self):
        view = GetNonValidatedRecords.as_view()
        request = self.factory.get(reverse('get-unvalidated-records'))
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_get_unvalidated_records_as_admin(self):
        view = GetNonValidatedRecords.as_view()
        request = self.factory.get(reverse('get-unvalidated-records'))
        request.user = self.admin_user
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_unvalidated_records_as_validator(self):
        view = GetNonValidatedRecords.as_view()
        BiologicalCollectionRecordF.create(
            original_species_name=u'Aves collection 1',
            site=self.location_site,
            validated=False,
            ready_for_validation=True,
            taxonomy=self.taxonomy_1
        )
        BiologicalCollectionRecordF.create(
            original_species_name=u'Aves collection 2',
            site=self.location_site,
            validated=False,
            ready_for_validation=True,
            taxonomy=self.taxonomy_2
        )
        user = UserF.create()
        content_type = ContentTypeF.create(
                app_label='bims',
                model='bims'
        )
        permission = PermissionF.create(
                name='Can validate Aves',
                content_type=content_type,
                codename='can_validate_aves'
        )
        group = GroupF.create()
        group.permissions.add(permission)
        user.groups.add(group)

        request = self.factory.get(reverse('get-unvalidated-records'))
        request.user = user
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 2)

    def test_only_get_aves_collection(self):
        from django.contrib.auth.models import Permission
        view = GetNonValidatedRecords.as_view()
        BiologicalCollectionRecordF.create(
            site=self.location_site,
            taxonomy=self.taxonomy_class_1,
            validated=False
        )
        user = UserF.create()
        permission = Permission.objects.filter(codename='can_validate_aves')[0]
        group = GroupF.create()
        group.permissions.add(permission)
        user.groups.add(group)

        request = self.factory.get(reverse('get-unvalidated-records'))
        request.user = user
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_referece_category(self):
        view = ReferenceCategoryList.as_view()
        BiologicalCollectionRecordF.create(
            original_species_name=u'Test name',
            site=self.location_site,
            reference_category=u'Database'
        )
        request = self.factory.get(reverse('list-reference-category'))
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)

    def test_get_module_summary(self):
        view = ModuleSummary.as_view()
        taxon_class_1 = TaxonomyF.create(
            scientific_name='Aves',
            rank=TaxonomicRank.CLASS.name
        )
        taxon_species_1 = TaxonomyF.create(
            scientific_name='Bird1',
            rank=TaxonomicRank.SPECIES.name,
            parent=taxon_class_1
        )
        BiologicalCollectionRecordF.create(
            taxonomy=taxon_species_1,
            validated=True,
            site=self.location_site
        )
        TaxonGroupF.create(
            name='Bird',
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
            taxonomies=(taxon_class_1,)
        )
        request = self.factory.get(reverse('module-summary'))
        response = view(request)
        self.assertTrue(len(response.data['Bird']) > 0)

    def test_get_autocomplete(self):
        view = autocomplete
        request = self.factory.get(
            '%s/?q=aves' % reverse('autocomplete-search'))
        response = view(request)
        self.assertTrue(response.status_code == 200)

        content = json.loads(response.content)
        self.assertTrue(len(content['results']) > 0)
