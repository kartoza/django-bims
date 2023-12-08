from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from bims.models.user_boundary import UserBoundary
from bims.tests.model_factories import UserBoundaryF

User = get_user_model()


class UserBoundaryAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.other_user = User.objects.create_user(username='otheruser', password='12345')
        self.client = APIClient()

        self.user_boundary = UserBoundaryF.create(
            user=self.user
        )
        self.other_user_boundary = UserBoundaryF.create(
            user=self.other_user
        )

    def test_unauthorized_access_list(self):
        url = reverse('list_user_boundary')
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_302_FOUND)

    def test_empty_user_boundary_list(self):
        self.client.login(
            username=self.user.username,
            password='12345'
        )
        UserBoundary.objects.filter(user=self.user).delete()
        url = reverse('list_user_boundary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access_detail(self):
        url = reverse('detail_user_boundary', kwargs={'id': self.user_boundary.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_access_other_user_boundary(self):
        self.client.login(
            username=self.user.username,
            password='12345'
        )
        url = reverse(
            'detail_user_boundary',
            kwargs={'id': self.other_user_boundary.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_unauthorized_user_boundary(self):
        url = reverse('delete_user_boundary', kwargs={'id': self.user_boundary.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_delete_other_user_boundary(self):
        self.client.login(
            username=self.user.username,
            password='12345'
        )
        url = reverse('delete_user_boundary', kwargs={'id': self.other_user_boundary.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
