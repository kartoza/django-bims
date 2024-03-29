# coding: utf-8
__author__ = 'Alison Mukoma <alison@kartoza.com>'
__copyright__ = 'kartoza.com'

import datetime
import logging
import ast

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView
from django.db.models import Q

from td_biblio.exceptions import DOILoaderError, PMIDLoaderError
from td_biblio.forms.bibliography import EntryBatchImportForm
from td_biblio.models import Author, Collection, Entry, Journal
from td_biblio.utils.loaders import DOILoader, PubmedLoader

logger = logging.getLogger('bims')


def superuser_required(function=None):
    """
    Decorator for views that checks that the user is a super user redirecting
    to the log-in page if necessary.

    Inspired by Django 'login_required' decorator
    """
    actual_decorator = user_passes_test(lambda u: u.is_superuser)
    if function:
        return actual_decorator(function)
    return actual_decorator


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class SuperuserRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(SuperuserRequiredMixin, cls).as_view(**initkwargs)
        return superuser_required(view)


class EntryListView(ListView):
    """Entry list view"""
    model = Entry
    paginate_by = 20
    template_name = '../templates/td_biblio/entry_list.html'

    def get(self, request, *args, **kwargs):
        """Check GET request parameters validity and store them"""

        # -- Publication year
        year = self.request.GET.get('year', None)

        # Is it an integer?
        if year:
            self.current_publication_date = datetime.date(int(year), 1, 1)
        else:
            self.current_publication_date = ''

        # -- Publication author
        author = self.request.GET.get('author', None)
        # Is it an integer?

        if author:
            self.current_publication_author = int(author)
        else:
            self.current_publication_author = ''

        # -- Publication collection
        collection = self.request.GET.get('collection', None)
        # Is it an integer?
        if collection:
            self.current_publication_collection = int(collection)
        else:
            self.current_publication_collection = ''

        # -- Search query
        search = self.request.GET.get('q', None)
        if search:
            self.query_search = search
        else:
            self.query_search = ''

        # -- DOI exist
        doi_exist = self.request.GET.get('doi_exist', '')
        try:
            self.doi_exist = ast.literal_eval(doi_exist)
        except SyntaxError:
            self.doi_exist = ''

        return super(EntryListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Add GET requests filters
        """
        filters = dict()

        # Publication date
        if self.current_publication_date:
            year = self.current_publication_date.year
            filters['publication_date__year'] = year

        # Publication authors
        if self.current_publication_author:
            filters['authors__id'] = self.current_publication_author

        # Publication collection
        if self.current_publication_collection:
            filters['collections__id'] = self.current_publication_collection

        # Base queryset
        qs = super(EntryListView, self).get_queryset()

        qs = qs.filter(**filters)

        # Query search
        if self.query_search:
            qs = qs.filter(
                Q(journal__name__icontains=self.query_search) |
                Q(journal__abbreviation__icontains=self.query_search) |
                Q(title__icontains=self.query_search)
            )


        # Doi exist
        if self.doi_exist != '':
            if not self.doi_exist:
                qs = qs.filter(doi='')
            else:
                qs = qs.exclude(doi='')

        # Return filtered queryset
        return qs

    def get_context_data(self, **kwargs):
        """
        Add filtering data to context
        """
        ctx = super(EntryListView, self).get_context_data(**kwargs)

        # -- Metrics
        # Publications (Entries)
        ctx['n_publications_total'] = Entry.objects.count()
        ctx['n_publications_filter'] = self.get_queryset().count()

        # Authors (from selected entries)
        ctx['n_authors_total'] = Author.objects.count()
        author_ids = self.get_queryset().values_list('authors__id', flat=True)
        author_ids = list(set(author_ids))
        filtered_authors = Author.objects.filter(id__in=author_ids)
        ctx['n_authors_filter'] = filtered_authors.count()

        # Journals (Entries)
        ctx['n_journals_total'] = Journal.objects.count()
        journal_ids = self.get_queryset().values_list('journal__id', flat=True)
        journal_ids = list(set(journal_ids))
        ctx['n_journals_filter'] = len(journal_ids)

        # -- Filters
        # publication date
        ctx['publication_years'] = self.get_queryset().dates(
            'publication_date',
            'year', order='DESC'
        )
        ctx['current_publication_year'] = self.current_publication_date

        # Publication author
        authors_order = ('last_name', 'first_name')
        ctx['publication_authors'] = filtered_authors.order_by(*authors_order)
        ctx['current_publication_author'] = self.current_publication_author

        # Publication collection
        ctx['publication_collections'] = Collection.objects.all()
        ctx['current_publication_collection'] = \
            self.current_publication_collection  # noqa

        # Search query
        ctx['current_query_search'] = self.query_search
        ctx['current_doi_filter'] = self.doi_exist

        return ctx


class EntryBatchImportView(LoginRequiredMixin,
                           SuperuserRequiredMixin,
                           FormView):

    form_class = EntryBatchImportForm
    template_name = '../templates/td_biblio/entry_import.html'
    success_url = reverse_lazy('td_biblio:entry_list')

    def form_valid(self, form):
        """Save to database"""
        # PMIDs
        pmids = form.cleaned_data['pmids']
        if len(pmids):
            pm_loader = PubmedLoader()

            try:
                pm_loader.load_records(PMIDs=pmids)
            except PMIDLoaderError as e:
                messages.error(self.request, e)
                return self.form_invalid(form)

            pm_loader.save_records()

        # DOIs
        dois = form.cleaned_data['dois']
        if len(dois):
            doi_loader = DOILoader()

            try:
                doi_loader.load_records(DOIs=dois)
            except DOILoaderError as e:
                messages.error(self.request, e)
                return self.form_invalid(form)

            doi_loader.save_records()

        messages.success(
            self.request,
            _("We have successfully imported {} reference(s).").format(
                len(dois) + len(pmids)
            )
        )

        return super(EntryBatchImportView, self).form_valid(form)
