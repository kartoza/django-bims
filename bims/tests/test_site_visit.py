from django.test import TestCase
from bims.tests.model_factories import SurveyF, UserF, Survey


class TestSiteVisitView(TestCase):
    """
    Test site visit view
    """
    def setUp(self):
        self.collector = UserF.create()
        self.owner = UserF.create()
        self.anonymous = UserF.create()
        self.superuser = UserF.create(
            is_superuser=True
        )
        self.survey = SurveyF.create(
            id=1,
            collector_user=self.collector,
            owner=self.owner
        )

    def test_SiteVisitView_update_non_logged_in(self):
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_SiteVisitView_update_ready_for_validation(self):
        self.survey.ready_for_validation = True
        self.survey.save()
        self.client.login(
            username=self.collector.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 403)

    def test_SiteVisit_validate(self):
        self.client.login(
            username=self.superuser.username,
            password='password'
        )
        response = self.client.get(
            '/api/validate-object/?pk={}'.format(self.survey.id)
        )
        self.assertEqual(response.status_code, 200)
        _survey = Survey.objects.get(id=self.survey.id)
        self.assertTrue(_survey.validated)

    def test_SiteVisit_reject(self):
        self.client.login(
            username=self.superuser.username,
            password='password'
        )
        self.survey.ready_for_validation = True
        response = self.client.get(
            '/api/reject-data/?pk={}'.format(self.survey.id)
        )
        self.assertEqual(response.status_code, 200)
        _survey = Survey.objects.get(id=self.survey.id)
        self.assertFalse(_survey.validated)
        self.assertFalse(_survey.ready_for_validation)

    def test_SiteVisitView_update_collector_access(self):
        self.client.login(
            username=self.collector.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 200)

    def test_SiteVisitView_update_owner_access(self):
        self.client.login(
            username=self.owner.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 200)

    def test_SiteVisitView_update_anonymous_access(self):
        self.client.login(
            username=self.anonymous.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 403)

    def test_SiteVisitView_update_superuser_access(self):
        self.client.login(
            username=self.superuser.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/update/1/'
        )
        self.assertEqual(response.status_code, 200)

    def test_SiteVisitView_detail_non_logged_in(self):
        response = self.client.get(
            '/site-visit/detail/1/'
        )
        self.assertEqual(response.status_code, 200)

    def test_SiteVisitView_detail_superuser(self):
        self.client.login(
            username=self.superuser.username,
            password='password'
        )
        response = self.client.get(
            '/site-visit/detail/1/'
        )
        self.assertContains(
            response,
            '<a class="btn btn-primary btn-normal" '
            'href="/site-visit/update/1/">Edit</a>'
        )
