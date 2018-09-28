from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    UserF,
    ContentTypeF,
    PermissionF,
    GroupF,
)
from bims.tests.model_factories import (
    LocationSiteF,
    TaxonF,
)
from bims.api_views.location_site import (
    LocationSiteList,
    LocationSiteDetail,
)
from bims.api_views.location_type import (
    LocationTypeAllowedGeometryDetail
)
from bims.api_views.non_validated_record import (
    GetNonValidatedRecords
)
from bims.api_views.taxon import TaxonDetail


class TestApiView(TestCase):
    """Test Location site API """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.location_site = LocationSiteF.create(
            pk=1,
            location_context_document='""'
        )
        self.fish_collection_1 = BiologicalCollectionRecordF.create(
            pk=1,
            original_species_name=u'Test fish species name 1',
            site=self.location_site
        )
        self.fish_collection_2 = BiologicalCollectionRecordF.create(
            pk=2,
            original_species_name=u'Test fish species name 2',
            site=self.location_site
        )
        self.admin_user = UserF.create(
            is_superuser=True,
            is_staff=True
        )

    def test_get_all_location(self):
        view = LocationSiteList.as_view()
        request = self.factory.get('/api/location-site/')
        response = view(request)
        self.assertTrue(len(response.data) > 0)

    def test_get_location_by_id(self):
        view = LocationSiteDetail.as_view()
        pk = '1'
        request = self.factory.get('/api/location-site/' + pk)
        response = view(request, pk)
        self.assertTrue(
            'id' in response.data
        )

    def test_get_taxon_by_id(self):
        pk = 1
        taxon = TaxonF.create(
            pk=1,
            common_name=u'Golden fish',
        )
        view = TaxonDetail.as_view()
        request = self.factory.get('/api/taxon/' + str(pk))
        response = view(request, str(pk))
        self.assertEqual(
            taxon.common_name,
            response.data['common_name']
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
        user = UserF.create()
        content_type = ContentTypeF.create(
                app_label='bims',
                model='bims'
        )
        permission = PermissionF.create(
                name='Can validate data',
                content_type=content_type,
                codename='can_validate_data'
        )
        group = GroupF.create()
        group.permissions.add(permission)
        user.groups.add(group)

        request = self.factory.get(reverse('get-unvalidated-records'))
        request.user = user
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_only_get_aves_collection(self):
        from django.contrib.auth.models import Permission
        view = GetNonValidatedRecords.as_view()
        taxon = TaxonF.create(
                taxon_class='Aves',
        )
        BiologicalCollectionRecordF.create(
                pk=3,
                site=self.location_site,
                taxon_gbif_id=taxon,
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
