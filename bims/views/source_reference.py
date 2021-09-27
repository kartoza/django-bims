import json
from django.views.generic import ListView, UpdateView, View, CreateView
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from geonode.base.models import HierarchicalKeyword, TaggedContentItem

from bims.utils.user import get_user_from_name
from bims.models.source_reference import (
    SourceReference,
    SourceReferenceBibliography,
    SourceReferenceDatabase,
    SourceReferenceDocument, DatabaseRecord
)
from td_biblio.models.bibliography import Author, AuthorEntryRank, Journal
from bims.models.bims_document import (
    BimsDocument,
    BimsDocumentAuthorship
)
from geonode.documents.models import Document
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.models.chemical_record import (
    ChemicalRecord
)


class SourceReferenceListView(ListView):
    model = SourceReference
    template_name = 'source_reference_list.html'
    paginate_by = 15
    source_reference_type = {
        'database': SourceReferenceDatabase,
        'bibliography': SourceReferenceBibliography,
        'document': SourceReferenceDocument
    }

    def get(self, request, *args, **kwargs):
        """Check GET request parameters validity and store them"""
        # -- Type query
        source_reference_type = self.request.GET.get('type', None)
        if source_reference_type:
            self.type_filter = source_reference_type
        else:
            self.type_filter = ''

        # -- Search query
        self.search_query = self.request.GET.get('q', '')

        # -- Collectors
        self.collectors = self.request.GET.get('collectors', None)
        if self.collectors:
            self.collectors = self.collectors.split(',')

        return super(SourceReferenceListView, self).get(
            request, *args, **kwargs)

    def get_queryset(self):
        """
        Add GET requests filters
        """
        filters = dict()
        # Base queryset
        qs = super(SourceReferenceListView, self).get_queryset()

        if self.collectors:
            qs = qs.filter(
                Q(sourcereferencebibliography__source__authors__user__in=
                  self.collectors) |
                Q(sourcereferencebibliography__document__bimsdocument__authors__in=  # noqa
                  self.collectors) |
                Q(sourcereferencedocument__source__bimsdocument__authors__in=
                  self.collectors) |
                Q(sourcereferencedocument__source__owner__in=self.collectors)
            )

        if self.type_filter:
            or_condition = Q()
            type_filters = self.type_filter.split(',')
            for type_filter in type_filters:
                if type_filter in self.source_reference_type:
                    or_condition |= Q(**{
                        'instance_of':
                            self.source_reference_type[type_filter]
                    })
                else:
                    for source_reference_type in self.source_reference_type:
                        or_condition &= Q(**{
                            'not_instance_of':
                                self.source_reference_type[
                                    source_reference_type]})
            qs = qs.filter(or_condition)

        if self.search_query:
            qs = qs.filter(
                Q(sourcereferencebibliography__source__title__icontains =
                  self.search_query) |
                Q(sourcereferencedocument__source__title__icontains =
                  self.search_query) |
                Q(sourcereferencedatabase__source__name__icontains =
                  self.search_query) |
                Q(note__icontains = self.search_query) |
                Q(source_name__icontains = self.search_query)
            )

        qs = qs.filter(**filters).distinct('id')

        # Return filtered queryset
        return qs

    def get_context_data(self, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.get_queryset()
        # - Get owner object from the id passed from the request
        collector_owner = None
        if self.request.GET.get('collectors'):
            try:
                ids = self.request.GET.get('collectors').split(',')
                user_model = get_user_model()
                collector_owner = user_model.objects.filter(
                    id__in=ids
                )
            except ValueError:
                # Couldn't parse the ids
                pass
        context['type'] = [
            {
                'title': 'Unpublished',
                'count': data.exclude(
                    Q(instance_of=SourceReferenceDatabase) |
                    Q(instance_of=SourceReferenceDocument) |
                    Q(instance_of=SourceReferenceBibliography)
                ).count(),
                'key': 'unpublished',
                'selected': 'unpublished' in self.type_filter
            },
            {
                'title': 'Database',
                'count': data.instance_of(
                    SourceReferenceDatabase
                ).count(),
                'key': 'database',
                'selected': 'database' in self.type_filter
            },
            {
                'title': 'Published report or thesis',
                'count': data.instance_of(
                    SourceReferenceDocument
                ).count(),
                'key': 'document',
                'selected': 'document' in self.type_filter
            },
            {
                'title': 'Peer-reviewed scientific article',
                'count': data.instance_of(
                    SourceReferenceBibliography
                ).count(),
                'key': 'bibliography',
                'selected': 'bibliography' in self.type_filter
            }
        ]
        context['search'] = self.search_query
        context['collector_owner'] = collector_owner
        return context


class DeleteSourceReferenceView(UserPassesTestMixin, View):

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        return self.request.user.has_perm('bims.change_sourcereference')

    def post(self, request, *args, **kwargs):
        reference_id = self.request.POST.get('reference_id', None)
        next_path = request.POST.get('next', reverse('source-references'))
        try:
            source_reference = SourceReference.objects.get(
                id=reference_id
            )
        except SourceReference.DoesNotExist:
            raise Http404('Source reference does not exist')
        source_reference_name = source_reference.title
        source_reference.delete()
        messages.success(
            request,
            'Source reference {} successfully deleted!'.format(
                source_reference_name
            ),
            extra_tags='source_reference')
        return HttpResponseRedirect(next_path)


class EditSourceReferenceView(UserPassesTestMixin, UpdateView):
    template_name = 'edit_source_reference.html'
    model = SourceReference
    fields = '__all__'

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        return self.request.user.has_perm('bims.change_sourcereference')

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        else:
            return reverse(
                'edit-source-reference',
                args=(
                    self.object.id,
                ))

    def get_user_from_string(self, user_string):
        """Return user object from string of user name"""
        first_name = user_string.split(' ')[0]
        last_name = ' '.join(user_string.split(' ')[1:])
        user = get_user_from_name(
            first_name=first_name,
            last_name=last_name
        )
        return user

    def update_published_report_reference(self, post_dict):
        order = 1
        year = post_dict.get('year', None)
        title = post_dict.get('title', None)
        source = post_dict.get('source', None)
        doc_url = post_dict.get('doc_url', None)
        doc_type = post_dict.get('doc_type', None)
        doc_file = self.request.FILES.get('doc_file', None)
        try:
            bims_doc = BimsDocument.objects.get(
                document__id=self.object.source.id)
        except BimsDocument.DoesNotExist:
            bims_doc = BimsDocument.objects.create(
                document=self.object.source
            )
        bims_doc.year = year
        bims_doc.authors.clear()
        # - Update title
        if title:
            self.object.source.title = title

        # - Update file
        if doc_type == 'doc_url' and doc_url:
            self.object.source.doc_url = doc_url
            self.object.source.doc_file = None
        elif doc_type == 'doc_file' and doc_file:
            self.object.source.doc_url = None
            self.object.source.doc_file = doc_file

        # - Update source
        if source:
            try:
                self.object.source.supplemental_information = json.dumps({
                    'document_source': source
                })
            except KeyError:
                pass
        for key in post_dict:
            author_user = None
            # From user id
            if 'author_id' in key:
                author_id = post_dict[key].strip()
                try:
                    author_user = get_user_model().objects.get(
                        id=author_id
                    )
                except get_user_model().DoesNotExist:
                    continue
            # From user name
            elif 'author' in key:
                user_string = post_dict[key].strip()
                author_user = self.get_user_from_string(user_string)
            if author_user:
                bims_doc_author, _ = (
                    BimsDocumentAuthorship.objects.get_or_create(
                        bimsdocument=bims_doc,
                        profile=author_user
                    )
                )
                bims_doc_author.ordering = order
                bims_doc_author.save()
            order += 1
        self.object.source.save()
        bims_doc.save()

    def update_bibliography_reference(self, post_dict):
        rank = 0
        title = post_dict.get('title', None)
        year = post_dict.get('year', None)
        doi = post_dict.get('doi', None)
        source = post_dict.get('source', None)
        source_id = post_dict.get('source_id', None)
        # - Check required fields
        if not title or not year:
            raise Http404('Incorrect POST body')
        # - Update title
        self.object.source.title = title
        # - Update year
        if year:
            self.object.source.publication_date = (
                self.object.source.publication_date.replace(
                    year=int(year)
                )
            )
        # - Update DOI
        if doi:
            self.object.source.doi = doi
        # - Update journal name
        if source_id:
            try:
                journal = Journal.objects.get(id=source_id)
                if source:
                    journal.name = source
                    journal.save()
                    self.object.source.journal = journal
                else:
                    self.object.source.journal = None
            except Journal.DoesNotExist:
                pass
        else:
            if source:
                journals = Journal.objects.filter(
                    name__iexact=source.strip()
                )
                if journals.exists():
                    self.object.source.journal = journals[0]
                else:
                    journal = Journal.objects.create(
                        name=source.strip()
                    )
                    self.object.source.journal = journal
        self.object.source.authors.clear()
        # - Update authors
        for key in post_dict:
            author_user = None
            if 'author_id' in key:
                author_id = post_dict[key].strip()
                try:
                    author_user = get_user_model().objects.get(
                        id=author_id
                    )
                except get_user_model().DoesNotExist:
                    continue
            elif 'author' in key:
                user_string = post_dict[key].strip()
                author_user = self.get_user_from_string(user_string)
            if author_user:
                try:
                    author = Author.objects.get(
                        user=author_user
                    )
                except Author.MultipleObjectsReturned:
                    author = Author.objects.filter(user=author_user)[0]
                except Author.DoesNotExist:
                    author = Author.objects.create(
                        first_name=author_user.first_name,
                        last_name=author_user.last_name,
                        user=author_user
                    )
                try:
                    author_entry_rank = AuthorEntryRank.objects.get(
                        author=author,
                        entry=self.object.source
                    )
                    author_entry_rank.rank = rank
                    author_entry_rank.save()
                except AuthorEntryRank.DoesNotExist:
                    AuthorEntryRank.objects.create(
                        author=author,
                        entry=self.object.source,
                        rank=rank
                    )
                    rank += 1
        self.object.source.save()

    def update_database_reference(self, post_dict):
        title = post_dict.get('title', '')
        source_name = post_dict.get('source_name', '')
        self.object.source_name = source_name
        self.object.source.name = title
        self.object.source.save()

    def update_unpublished(self, post_dict):
        title = post_dict.get('title', '')
        source_name = post_dict.get('source_name', '')
        self.object.note = title
        self.object.save()
        source_references = SourceReference.objects.filter(
            note=title.strip(),
            source_name=source_name.strip()
        ).exclude(
            Q(instance_of=SourceReferenceDatabase) |
            Q(instance_of=SourceReferenceBibliography) |
            Q(instance_of=SourceReferenceDocument)
        )
        if source_references.count() > 1:
            source_reference = source_references[0]
            BiologicalCollectionRecord.objects.filter(
                source_reference__in=source_references
            ).update(source_reference=source_reference)
            ChemicalRecord.objects.filter(
                source_reference__in=source_references
            ).update(source_reference=source_reference)
            source_references.exclude(id=source_reference.id).delete()

    def form_valid(self, form):
        post_dict = self.request.POST.dict()
        if self.object.is_published_report():
            self.update_published_report_reference(
                post_dict
            )
        elif self.object.is_database():
            self.update_database_reference(
                post_dict
            )
        elif self.object.is_bibliography():
            self.update_bibliography_reference(
                post_dict
            )
        else:
            self.update_unpublished(
                post_dict
            )

        return super(EditSourceReferenceView, self).form_valid(
            form
        )

    def get_context_data(self, **kwargs):
        context = super(
            EditSourceReferenceView, self).get_context_data(**kwargs)
        context['past_url'] = self.request.GET.get('next')
        if self.object.is_published_report():
            try:
                context['source_name'] = json.loads(
                    self.object.source.supplemental_information
                )['document_source']
            except:  # noqa
                pass
        return context


class AddSourceReferenceView(UserPassesTestMixin, CreateView):
    template_name = 'source_references/add_source_reference.html'
    model = SourceReference
    fields = '__all__'
    success_url = '/add-source-reference/'

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        return self.request.user.has_perm('bims.change_sourcereference')

    def handle_database_record(self, post_data):
        if (
                DatabaseRecord.objects.filter(
                    name__iexact=self.request.POST.get('name')).exists()
        ):
            messages.add_message(
                self.request,
                messages.ERROR,
                'Database already exists',
                extra_tags='source-reference'
            )
            return False
        else:
            database_record = DatabaseRecord.objects.create(
                name=post_data.get('name'),
                description=post_data.get('description', ''),
                url=post_data.get('url', '')
            )
            SourceReferenceDatabase.objects.create(
                source=database_record
            )
        return True

    def handle_published_report(self, post_data, file_data):
        if (
            SourceReferenceDocument.objects.filter(
                source__title__iexact=post_data.get('name')
            ).exists()
        ):
            messages.add_message(
                self.request,
                messages.ERROR,
                'Published report already exists',
                extra_tags='source_reference'
            )
            return False

        document, _ = Document.objects.get_or_create(
            owner=self.request.user,
            is_published=True,
            abstract=post_data.get('description', ''),
            title=post_data.get('title', ''),
            doc_type=post_data.get('doc_type', None),
            doc_file=file_data.get('report_file', None),
            doc_url=post_data.get('report_url', None),
            supplemental_information=json.dumps({
                'document_source': post_data.get('source')
            })
        )

        # tag keyword of document as Bims Source Reference
        keyword = None
        try:
            keyword = HierarchicalKeyword.objects.get(
                slug='bims_source_reference')
        except HierarchicalKeyword.DoesNotExist:
            try:
                last_keyword = HierarchicalKeyword.objects.filter(
                    depth=1).order_by('path').last()
                if not last_keyword:
                    path = '0000'
                else:
                    path = last_keyword.path
                path = "{:04d}".format(int(path) + 1)
                keyword, created = HierarchicalKeyword.objects.get_or_create(
                    slug='bims_source_reference',
                    name='Bims Source Reference',
                    depth=1,
                    path=path)
            except Exception:  # noqa
                pass
        if keyword:
            TaggedContentItem.objects.get_or_create(
                content_object=document, tag=keyword)

        bims_document = BimsDocument.objects.create(
            document=document,
            year=post_data.get('year', None),
        )

        # Update authors
        try:
            author_ids = post_data.get('author_ids', None)
            if author_ids:
                bims_document.authors.clear()
                author_ids = author_ids.split(',')
                for author_id in author_ids:
                    bims_document.authors.add(author_id)
        except KeyError:
            pass

        SourceReferenceDocument.objects.create(
            source=document
        )

        return True

    def get_context_data(self, **kwargs):
        context = super(
            AddSourceReferenceView, self).get_context_data(**kwargs)
        reference_type = [
            'Unpublished',
            'Database',
            'Published report or thesis',
            'Peer-reviewed scientific article'
        ]
        context['params'] = {
            'reference_type': json.dumps(reference_type)
        }.items()
        return context

    def form_valid(self, form):
        post_dict = self.request.POST.dict()
        file_dict = self.request.FILES.dict()
        reference_type = self.request.POST.get('reference_type')
        processed = False
        if 'database' in reference_type.lower():
            processed = self.handle_database_record(post_data=post_dict)
        elif 'published report' in reference_type.lower():
            processed = self.handle_published_report(
                post_data=post_dict,
                file_data=file_dict
            )

        if not processed:
            return self.form_invalid(form)

        return super(AddSourceReferenceView, self).form_valid(
            form
        )
