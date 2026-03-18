# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Tests for Authentication API v1.

Made with love by Kartoza | https://kartoza.com
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bims.tests.model_factories import UserF


User = get_user_model()


class AuthAPITestCase(TestCase):
    """Test cases for the Auth API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = UserF(
            username='testuser',
            email='test@example.com',
        )
        self.user.set_password('TestPassword123!')
        self.user.save()

    def test_get_csrf_token(self):
        """Test getting CSRF token."""
        response = self.client.get('/api/v1/auth/csrf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('csrfToken', response.data['data'])

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'testuser',
            'password': 'TestPassword123!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['meta']['message'], 'Login successful')

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'testuser',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_inactive_user(self):
        """Test login with inactive user."""
        self.user.is_active = False
        self.user.save()

        response = self.client.post('/api/v1/auth/login/', {
            'username': 'testuser',
            'password': 'TestPassword123!',
        })
        # Inactive users should not be able to authenticate
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        """Test successful logout."""
        # Login first
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/v1/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['meta']['message'], 'Logout successful')

    def test_logout_unauthenticated(self):
        """Test logout when not authenticated."""
        response = self.client.post('/api/v1/auth/logout/')
        # Should still return success (logging out when not logged in is OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register_success(self):
        """Test successful registration."""
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'NewUserPassword123!',
            'password2': 'NewUserPassword123!',
            'first_name': 'New',
            'last_name': 'User',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['username'], 'newuser')

        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_missing_required_fields(self):
        """Test registration with missing required fields."""
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            # Missing email and password
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_register_password_mismatch(self):
        """Test registration with password mismatch."""
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'Password123!',
            'password2': 'DifferentPassword123!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('password2', response.data['errors'])

    def test_register_duplicate_username(self):
        """Test registration with existing username."""
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'testuser',  # Already exists
            'email': 'another@example.com',
            'password1': 'Password123!',
            'password2': 'Password123!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('username', response.data['errors'])

    def test_register_duplicate_email(self):
        """Test registration with existing email."""
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'anotheruser',
            'email': 'test@example.com',  # Already exists
            'password1': 'Password123!',
            'password2': 'Password123!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('email', response.data['errors'])

    def test_register_weak_password(self):
        """Test registration with weak password."""
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': '123',  # Too short/weak
            'password2': '123',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('password1', response.data['errors'])

    def test_get_user_authenticated(self):
        """Test getting current user info when authenticated."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/v1/auth/user/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['email'], 'test@example.com')

    def test_get_user_unauthenticated(self):
        """Test getting user info when not authenticated."""
        response = self.client.get('/api/v1/auth/user/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        """Test updating user profile."""
        self.client.force_authenticate(user=self.user)

        response = self.client.patch('/api/v1/auth/update_profile/', {
            'first_name': 'Updated',
            'last_name': 'Name',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # Refresh user and verify
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_update_profile_unauthenticated(self):
        """Test updating profile when not authenticated."""
        response = self.client.patch('/api/v1/auth/update_profile/', {
            'first_name': 'Updated',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password(self):
        """Test changing password."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/v1/auth/change_password/', {
            'current_password': 'TestPassword123!',
            'new_password': 'NewPassword456!',
            'confirm_password': 'NewPassword456!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword456!'))

    def test_change_password_wrong_current(self):
        """Test changing password with wrong current password."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/v1/auth/change_password/', {
            'current_password': 'WrongPassword!',
            'new_password': 'NewPassword456!',
            'confirm_password': 'NewPassword456!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_change_password_mismatch(self):
        """Test changing password with confirmation mismatch."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/v1/auth/change_password/', {
            'current_password': 'TestPassword123!',
            'new_password': 'NewPassword456!',
            'confirm_password': 'DifferentPassword!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_change_password_unauthenticated(self):
        """Test changing password when not authenticated."""
        response = self.client.post('/api/v1/auth/change_password/', {
            'current_password': 'TestPassword123!',
            'new_password': 'NewPassword456!',
            'confirm_password': 'NewPassword456!',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
