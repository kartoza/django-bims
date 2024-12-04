
from django.core.cache import cache
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.models.search_process import SearchProcess
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED

from bims.tests.model_factories import UserF


class ClearCacheViewTest(FastTenantTestCase):

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

        # Create the tenant-specific client
        self.client = TenantClient(self.tenant)

        # Create sample SearchProcess objects
        SearchProcess.objects.create(finished=True, locked=False)
        SearchProcess.objects.create(finished=True, locked=True)

        # Populate the cache
        cache.set("test_key", "test_value")

    def test_clear_cache_superuser(self):
        # Authenticate as the superuser
        self.client.login(username=self.superuser.username, password="password")

        # Make the POST request
        response = self.client.post("/api/clear-cache/")

        # Assertions
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {"message": "Cache cleared successfully."})

        # Verify cache is cleared
        self.assertIsNone(cache.get("test_key"))

        # Verify finished and unlocked SearchProcess objects are deleted
        self.assertEqual(SearchProcess.objects.filter(finished=True, locked=False).count(), 0)

        # Verify finished and locked SearchProcess objects remain
        self.assertEqual(SearchProcess.objects.filter(finished=True, locked=True).count(), 1)

    def test_clear_cache_non_superuser(self):
        # Authenticate as a regular user
        self.client.login(username="user", password="password")

        # Make the POST request
        response = self.client.post("/api/clear-cache/")

        # Assertions
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"detail": "You do not have permission to perform this action."})

        # Verify cache is not cleared
        self.assertEqual(cache.get("test_key"), "test_value")

    def test_clear_cache_unauthenticated(self):
        # Make the POST request without authentication
        response = self.client.post("/api/clear-cache/")

        # Assertions
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {"detail": "Authentication credentials were not provided."})

    def test_clear_cache_invalid_method(self):
        # Authenticate as the superuser
        self.client.login(username="admin", password="password")

        # Make a GET request
        response = self.client.get("/api/clear-cache/")

        # Assertions
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
