from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.models import LocationSite
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED

from bims.tests.model_factories import UserF, LocationContextF, LocationSiteF, SurveyF


class DeleteDanglingSitesTest(FastTenantTestCase):

    def setUp(self):
        # Call super to set up the tenant
        super().setUp()

        # Create a superuser
        self.superuser = UserF.create(
            is_superuser=True
        )

        # Create a regular user
        self.user = UserF.create(
            username="user",
            password="password",
        )
        self.client = TenantClient(self.tenant)

        self.dangling_site = LocationSiteF()
        self.site = LocationSiteF()
        SurveyF.create(
            site=self.site
        )
        LocationContextF.create(
            site=self.dangling_site
        )

    def test_delete_dangling_sites_superuser(self):
        # Authenticate as the superuser
        self.client.login(username=self.superuser.username, password="password")

        # Make the POST request
        response = self.client.post("/api/delete-dangling-sites/")

        # Assertions
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {"message": "Deleting dangling sites in the background."})

        self.assertFalse(
            LocationSite.objects.filter(
                id=self.dangling_site.id
            ).exists()
        )

        self.assertTrue(
            LocationSite.objects.filter(
                id=self.site.id
            ).exists()
        )

    def test_delete_dangling_sites_non_superuser(self):
        # Authenticate as a regular user
        self.client.login(username="user", password="password")

        # Make the POST request
        response = self.client.post("/api/delete-dangling-sites/")

        # Assertions
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"detail": "You do not have permission to perform this action."})

        # Verify site is not deleted
        self.assertTrue(
            LocationSite.objects.filter(
                id=self.dangling_site.id
            ).exists()
        )

    def test_delete_dangling_sites_unauthenticated(self):
        # Make the POST request without authentication
        response = self.client.post("/api/delete-dangling-sites/")

        # Assertions
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {"detail": "Authentication credentials were not provided."})

    def test_delete_dangling_sites_invalid_method(self):
        # Authenticate as the superuser
        self.client.login(username="admin", password="password")

        # Make a GET request
        response = self.client.get("/api/delete-dangling-sites/")

        # Assertions
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
