# -*- coding: utf-8 -*-
"""
Django TailorDev Biblio

Test views
"""
import datetime
import pytest

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

from ..factories import (CollectionFactory, EntryWithAuthorsFactory)
from ..models import Entry


@pytest.mark.django_db
class EntryListViewTests(TestCase):
    """
    Tests for the EntryListView
    """

    def setUp(self):
        """
        Generate Author and Entry fixtures & set object level vars
        """
        self.url = reverse('td_biblio:entry_list')
        self.paginate_by = 20
        self.n_publications_per_year = 3
        self.start_year = 2000
        self.end_year = 2014
        self.n_publications = self.end_year - self.start_year
        self.n_publications *= self.n_publications_per_year
        self.n_authors = self.n_publications * 3
        self.publications_years = []
        self.max_page_num = self.n_publications / self.paginate_by
        if self.n_publications % self.paginate_by:
            self.max_page_num += 1

        # Entry (14 * 3 = 42)
        for y in range(self.start_year, self.end_year, 1):
            for i in range(1, 1 + self.n_publications_per_year):
                date = datetime.date(y, i, 1)
                EntryWithAuthorsFactory(publication_date=date)
                self.publications_years.append(y)

    def test_get(self):
        """
        Test the EntryListViewTests get method
        """
        response = self.client.get(self.url)

        # Standard response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('td_biblio/entry_list.html')

    def _test_one_page(self, page=1, **kwargs):
        """
        Test the get request pagination for one page.

        Use **kwargs to add request parameters.
        """
        params = {'page': page}
        params.update(kwargs)
        response = self.client.get(self.url, params)

        # Check the requested page number is within the proper range
        if page > self.max_page_num:
            self.assertEqual(response.status_code, 404)
            return

        # Standard response
        self.assertEqual(response.status_code, 200)

        # Publication list
        publication_block = '<li class="publication-list-year">'
        start = self.paginate_by * (page - 1)
        end = self.paginate_by * page
        if end > self.n_publications:
            end = self.n_publications
        expected_count = len(set(self.publications_years[start:end]))
        self.assertContains(response, publication_block,
                            count=expected_count)

        publication_block = '<li class="publication">'
        self.assertContains(response, publication_block,
                            count=end - start)

        # Pagination
        self.assertTrue(response.context['is_paginated'])

        pagination_block = '<div class="pagination-centered">'
        self.assertContains(response, pagination_block)

        pagination_block = '<a href="">%d</a>' % page
        self.assertContains(response, pagination_block)

    def _test_filtering(self, **kwargs):
        """Test entry list filtering"""
        params = dict()
        params.update(kwargs)
        response = self.client.get(self.url, params)

        # Standard response
        self.assertEqual(response.status_code, 200)

        # Display at list a publication
        publication_block = '<li class="publication">'
        self.assertContains(response, publication_block)

    def test_pagination(self):
        """
        Test the get request pagination for 4 pages
        """
        for page in range(1, 5):
            self._test_one_page(page=page)

    def test_year_filtering(self):
        """
        Test the get request with a year parameter
        """
        # Get a valid date
        entry = Entry.objects.get(id=1)
        params = {'year': entry.publication_date.year}

        self._test_filtering(**params)

    def test_author_filtering(self):
        """
        Test the get request with an author parameter
        """
        # Get a valid author
        entry = Entry.objects.get(id=1)
        params = {'author': entry.first_author.id}

        self._test_filtering(**params)

    def test_collection_filtering(self):
        """
        Test the get request with a collection parameter
        """
        # Create a collection
        entries = Entry.objects.filter(id__in=(1, 5, 10, 15))
        collection = CollectionFactory(entries=entries)

        # Get a valid collection
        params = {'collection': collection.id}

        self._test_filtering(**params)

    def test_collection_author_year_filtering(self):
        """
        Test the get request with a collection, an author and a year parameter
        """
        # Create a collection
        entries = Entry.objects.filter(id__in=(1, 5, 10, 15))
        collection = CollectionFactory(entries=entries)
        entry = Entry.objects.get(id=1)

        # Get a valid collection
        params = {
            'collection': collection.id,
            'author': entry.first_author.id,
            'year': entry.publication_date.year,
        }
        self._test_filtering(**params)

    def test_author_year_filtering(self):
        """
        Test the get request with an author and a year parameter
        """
        # Get a valid date
        entry = Entry.objects.get(id=1)
        params = {
            'author': entry.first_author.id,
            'year': entry.publication_date.year,
        }

        self._test_filtering(**params)

    def test_get_queryset(self):
        """
        Test the EntryListViewTests get_queryset method
        """
        year = 2012
        response = self.client.get(self.url, {'year': year})
        self.assertEqual(response.status_code, 200)

        # Context
        date = datetime.date(year, 1, 1)
        self.assertEqual(response.context['current_publication_year'], date)

        self.assertEqual(
            response.context['n_publications_filter'],
            self.n_publications_per_year)

    def test_get_context_data(self):
        """
        Test the EntryListViewTests get_context_data method
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Get all different publication years
        start = self.end_year - 1
        end = self.start_year - 1
        years_range = range(start, end, -1)
        publication_years = [datetime.date(y, 1, 1) for y in years_range]

        # Context
        self.assertEqual(
            response.context['n_publications_total'],
            self.n_publications)

        self.assertEqual(
            response.context['n_publications_filter'],
            self.n_publications)

        self.assertListEqual(
            list(response.context['publication_years']),
            publication_years)

        self.assertEqual(
            response.context['n_authors_total'],
            self.n_authors)

        self.assertEqual(
            response.context['publication_authors'].count(),
            self.n_authors)

        self.assertEqual(response.context['current_publication_year'], None)


@pytest.mark.django_db
class EntryBatchImportViewTests(TestCase):
    """
    Tests for the EntryBatchImportView
    """

    def setUp(self):
        self.url = reverse('td_biblio:import')
        User = get_user_model()
        self.fake_password = 'fake123'
        self.superuser = User.objects.create_superuser(
            'louis', 'louis@pasteur.com', self.fake_password
        )
        self.user = User.objects.create_user(
            'james', 'james@watson.com', self.fake_password
        )

    def test_user_must_be_a_logged_superuser(self):
        """Test the EntryBatchImportView for login restriction"""
        response = self.client.get(self.url)

        login_redirect_url = '{}?next={}'.format(
            settings.LOGIN_URL,
            self.url
        )

        # User is not logged in: it should redirect to login view
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, login_redirect_url)

        # Log user as a normal user
        self.client.login(
            username=self.user.username,
            password=self.fake_password
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, login_redirect_url)

        # Log user as a normal user
        self.client.login(
            username=self.user.username,
            password=self.fake_password
        )

        # A standard user should be redirected to the login page
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, login_redirect_url)

        # Log user as a super user
        self.client.login(
            username=self.superuser.username,
            password=self.fake_password
        )

        # A super user should not be redirected
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('td_biblio/entry_import.html')

    def test_get(self):
        """
        Test the EntryBatchImportView get method
        """
        self.client.login(
            username=self.superuser.username,
            password=self.fake_password
        )
        response = self.client.get(self.url)

        # Standard response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('td_biblio/entry_import.html')

    def test_post(self):
        """
        Test the EntryBatchImportView post method
        """
        self.client.login(
            username=self.superuser.username,
            password=self.fake_password
        )

        self.assertEqual(Entry.objects.count(), 0)

        data = {
            'pmids': '26588162,19569182',
            'dois': '10.1093/nar/gks419,10.1093/nar/gkp323'
        }

        # Redirect on success
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Entry.objects.count(), 4)

        # Follow redirection to test success view
        response = self.client.post(self.url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            'td_biblio/entry_list.html'
        )

        # Test messages
        response_messages = response.context['messages']
        # We have two messages (we did the same request two times)
        self.assertEqual(len(response_messages), 2)
        for m in response_messages:
            self.assertEqual(
                str(m),
                'We have successfully imported 4 reference(s).'
            )
            self.assertEqual(m.level, messages.SUCCESS)
