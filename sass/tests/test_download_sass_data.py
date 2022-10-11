import os.path
import csv
import factory
from django.db.models import signals
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from bims.tests.model_factories import (
    UserF,
)
from sass.tests.model_factories import (
    SiteVisitF,
    SiteVisitTaxonF
)


class TestDownloadSassView(TestCase):
    def setUp(self) -> None:
        self.user = UserF.create()
        self.client = APIClient()
        self.csv_file = None

    def tearDown(self) -> None:
        if self.csv_file:
            if os.path.exists(self.csv_file):
                os.remove(self.csv_file)

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_download_no_sass_record(self):
        self.client.login(
            username=self.user.username,
            password='password'
        )
        site_visit = SiteVisitF.create()
        response = self.client.get(
            f'/sass/download-sass-taxon-data/?siteVisitId={site_visit.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'No SASS taxon data')

    @factory.django.mute_signals(signals.post_save, signals.pre_save)
    def test_download_sass_record(self):
        self.client.login(
            username=self.user.username,
            password='password'
        )
        site_visit = SiteVisitF.create()
        svt1 = SiteVisitTaxonF.create(
            site_visit=site_visit
        )
        svt2 = SiteVisitTaxonF.create(
            site_visit=site_visit
        )
        svt3 = SiteVisitTaxonF.create(
            site_visit=site_visit
        )
        response = self.client.get(
            f'/sass/download-sass-taxon-data/?siteVisitId={site_visit.id}'
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        file_name = response_data['message']
        self.csv_file = os.path.join(
            settings.MEDIA_ROOT,
            'processed_csv',
            file_name
        )
        sass_score = (
            svt1.sass_taxon.sass_5_score +
            svt2.sass_taxon.sass_5_score +
            svt3.sass_taxon.sass_5_score
        )
        taxa_number = 3
        aspt_score = round(sass_score/taxa_number, 2)
        with open(self.csv_file, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if 'SASS SCORE' in row:
                    self.assertEqual(row[1], str(sass_score))
                if 'ASPT' in row:
                    self.assertEqual(row[1], str(aspt_score))
        self.assertTrue(os.path.exists(self.csv_file))
