import json
import logging
import threading
import time
from unittest.mock import patch

from django.db.models.signals import post_save
from django.test import TransactionTestCase, TestCase
from bims.models import LocationSite, location_site_post_save_handler
from bims.tests.model_factories import (
    SurveyF, UserF, Survey,
    BiologicalCollectionRecordF, BiologicalCollectionRecord, LocationSiteF,
    TaxonomyF, ChemicalRecordF
)

LOGGER = logging.getLogger(__name__)


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

    def test_SiteVisit_validate_with_unvalidated_species(self):
        taxon = TaxonomyF.create(
            validated=False
        )
        BiologicalCollectionRecordF.create(
            taxonomy=taxon,
            survey=self.survey
        )
        self.client.login(
            username=self.superuser.username,
            password='password'
        )
        self.survey.ready_for_validation = True
        self.survey.save()
        response = self.client.get(
            '/api/validate-object/?pk={}'.format(self.survey.id)
        )
        self.assertEqual(response.status_code, 400)

    def test_SiteVisit_validate(self):
        self.client.login(
            username=self.superuser.username,
            password='password'
        )
        self.survey.ready_for_validation = True
        self.survey.save()
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
            '/api/reject-site-visit/?pk={}'.format(self.survey.id)
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

    def test_SiteVisitView_update_add_new_collection(self):
        self.client.login(
            username=self.owner.username,
            password='password'
        )
        bio_1 = BiologicalCollectionRecordF.create(
            survey=self.survey
        )
        bio_1_id = bio_1.id
        taxon = TaxonomyF.create()
        post_data = {
            'collection-id-list': '{}'.format(bio_1_id),
            'taxa-id-list': '{}'.format(taxon.id),
            '{}-observed'.format(taxon.id): 'True',
            '{}-abundance'.format(taxon.id): 12,
            'owner_id': self.owner.id,
            'collector_id': self.collector.id,
            'site': self.survey.site.id,
            'date': '2021-07-09',
            'end_embargo_date': '2022-09-09'
        }
        self.client.post(
            '/site-visit/update/1/',
            post_data
        )
        bio = BiologicalCollectionRecord.objects.filter(
            survey=self.survey
        )
        self.assertEqual(bio.count(), 2)
        self.assertEqual(str(bio[0].end_embargo_date), '2022-09-09')

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
            'date': '2021-07-09',
            'owner_id': 9999,
            'collector_id': 9999
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


class TestSiteVisitDelete(TransactionTestCase):
    def setUp(self):
        post_save.disconnect(receiver=location_site_post_save_handler, sender=LocationSite)
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

    def test_SiteVisitView_delete(self):
        # Delete site visit
        location_site = LocationSiteF.create()

        survey_1 = SurveyF.create(
            collector_user=self.collector,
            owner=self.owner,
            site=location_site
        )

        survey_2 = SurveyF.create(
            collector_user=self.collector,
            owner=self.owner,
            site=location_site
        )

        bio = BiologicalCollectionRecordF.create(
            survey=survey_1
        )

        res = self.client.login(
            username=self.superuser.username,
            password='password'
        )

        ChemicalRecordF.create(
            location_site=location_site
        )

        post_data = {}

        original_thread_start = threading.Thread.start

        def mock_start(self, *args, **kwargs):
            original_thread_start(self, *args, **kwargs)
            self.join()

        with patch.object(threading.Thread, 'start', new=mock_start):
            self.client.post(
                '/site-visit/delete/{}/'.format(
                    survey_1.id
                ),
                post_data,
                follow=True
            )

            self.assertFalse(
                Survey.objects.filter(id=survey_1.id).exists()
            )

            self.assertFalse(
                BiologicalCollectionRecord.objects.filter(
                    survey_id=survey_1.id).exists()
            )

            self.assertTrue(
                LocationSite.objects.filter(
                    id=location_site.id).exists()
            )

    def tearDown(self):
        post_save.connect(receiver=location_site_post_save_handler, sender=LocationSite)

