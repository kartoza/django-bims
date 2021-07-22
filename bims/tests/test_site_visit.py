import json
from django.test import TestCase
from bims.tests.model_factories import (
    SurveyF, UserF, Survey,
    BiologicalCollectionRecordF, BiologicalCollectionRecord
)


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

    def test_SiteVisitView_delete_records(self):
        # Delete records by owner
        survey = Survey.objects.get(id=self.survey.id)
        survey.validated = True
        survey.save()
        self.client.login(
            username=self.owner.username,
            password='password'
        )
        bio = BiologicalCollectionRecordF.create(
            survey=self.survey
        )
        bio_id = bio.id
        bio_1 = BiologicalCollectionRecordF.create(
            survey=self.survey
        )
        bio_1_id = bio_1.id
        post_data = {
            'collection-id-list': [bio_1.id],
            'site': self.survey.site.id,
            'date':'2021-07-09'
        }
        response = self.client.post(
            '/site-visit/update/1/',
            post_data
        )
        self.assertEqual(response.status_code, 302)
        bio = BiologicalCollectionRecord.objects.filter(
            survey=self.survey
        )
        self.assertFalse(Survey.objects.get(id=self.survey.id).validated)
        self.assertNotEqual(bio.count(), 1)
        self.assertTrue(BiologicalCollectionRecord.objects.filter(
            id=bio_1_id
        ).exists())

        # Delete records by superuser
        survey.validated = True
        survey.save()
        self.client.login(
            username=self.superuser.username,
            password='password'
        )
        self.client.post(
            '/site-visit/update/1/',
            post_data
        )
        bio = BiologicalCollectionRecord.objects.filter(
            survey=self.survey
        )
        self.assertEqual(bio.count(), 1)
        self.assertFalse(BiologicalCollectionRecord.objects.filter(
            id=bio_id
        ).exists())
        self.assertTrue(Survey.objects.get(id=self.survey.id).validated)
