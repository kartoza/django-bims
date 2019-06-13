from django.test import TestCase

from bims.tests.model_factories import (
    LocationSiteF,
    UserF
)


class TestLocationSiteFormView(TestCase):
    """
    Tests location site form.
    """
    def setUp(self):
        """
        Sets up before each test
        """
        pass

    def test_LocationSiteFormView_non_logged_in_user_access(self):
        """
        Tests open form for non logged in user
        """
        response = self.client.get(
            '/location-site-form/add/'
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_LocationSiteFormView_logged_in_user_access(self):
        """
        Tests open form for logged in user
        """
        user = UserF.create()
        self.client.login(
            username=user.username,
            password='password'
        )
        response = self.client.get(
            '/location-site-form/add/'
        )
        self.assertEqual(response.status_code, 200)
