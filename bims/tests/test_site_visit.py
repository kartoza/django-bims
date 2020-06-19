from django.test import TestCase
from bims.tests.model_factories import SurveyF, UserF


class TestSiteVisitView(TestCase):
    """
    Test site visit view
    """
    def setUp(self):
        self.survey = SurveyF.create(id=1)

    def test_SiteVisitView_non_logged_in(self):
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_SiteVisitView_update_collector_access(self):
        user = UserF.create()
        self.survey.collector_user=user
        self.survey.save()
        self.client.login(
            username=user.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 200)

    def test_SiteVisitView_update_owner_access(self):
        user = UserF.create()
        self.survey.owner = user
        self.survey.save()
        self.client.login(
            username=user.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 200)

    def test_SiteVisitView_update_anonymous_access(self):
        user = UserF.create()
        self.client.login(
            username=user.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 403)

    def test_SiteVisitView_update_superuser_access(self):
        user = UserF.create(
            is_superuser=True
        )
        self.client.login(
            username=user.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 200)
