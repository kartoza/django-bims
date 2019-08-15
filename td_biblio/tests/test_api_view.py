from td_biblio.tests.model_factories import (
    AuthorF,
    JournalF,
    EntryF
)
from rest_framework.test import APIRequestFactory
from django.test import TestCase
from bims.tests.model_factories import UserF
from td_biblio.api_views.bibliography import GetBibliographyByDOI


class TestApiView(TestCase):
    """Test Location site API """

    def setUp(self):
        self.admin_user = UserF.create(
            is_superuser=True,
            is_staff=True
        )
        self.journal_title = 'test title'
        self.doi = '10.1111/GCCE.2018.1111111'
        self.factory = APIRequestFactory()
        self.journal = JournalF.create(
            pk=1,
            name='journal'
        )
        self.author = AuthorF.create(
            pk=1,
            first_name='First',
            last_name='Last',
        )
        self.entry = EntryF.create(
            pk=1,
            title=self.journal_title,
            journal=self.journal,
            doi=self.doi
        )

    def test_fetch_bibliography_by_doi_wrong_format(self):
        view = GetBibliographyByDOI.as_view()
        request = self.factory.get(
            '/bibliography/api/fetch/by-doi/?q=11.1111/GCCE.1111.1111111')
        request.user = self.admin_user
        response = view(request)
        self.assertEqual(
            response.status_code, 400
        )

    def test_fetch_bibliography_by_doi(self):
        view = GetBibliographyByDOI.as_view()
        request = self.factory.get(
            '/bibliography/api/fetch/by-doi/?q=' + self.doi)
        request.user = self.admin_user
        response = view(request)
        self.assertEqual(
            response.status_code, 200
        )
        self.assertEqual(
            response.data['doi'], self.doi
        )
