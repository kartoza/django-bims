import json
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.conf import settings
from django.urls import reverse
from django.views.generic import UpdateView, CreateView

from geonode.base.models import (
    HierarchicalKeyword, TaggedContentItem
)
from geonode.documents.models import Document
from geonode.documents.forms import DocumentCreateForm

from bims.models.bims_document import BimsDocument
from bims.utils.user import get_user_from_name
from bims.utils.user import create_users_from_string

logger = logging.getLogger("geonode.documents.views")

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this document")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this document.")
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this document")
_PERMISSION_MSG_METADATA = _(
        "You are not permitted to modify this document's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this document")


ALLOWED_DOC_TYPES = settings.ALLOWED_DOCUMENT_TYPES


class DocumentUploadView(CreateView):
    template_name = 'documents/document_upload.html'
    form_class = DocumentCreateForm

    def get_context_data(self, **kwargs):
        context = super(DocumentUploadView, self).get_context_data(**kwargs)
        context['ALLOWED_DOC_TYPES'] = ALLOWED_DOC_TYPES
        return context

    def form_invalid(self, form):
        if self.request.GET.get('no__redirect', False):
            out = {'success': False}
            out['message'] = ""
            status_code = 400
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=status_code)
        else:
            form.name = None
            form.title = None
            form.doc_file = None
            form.doc_url = None
            return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save(commit=False)
        self.object.owner = self.request.user

        if settings.ADMIN_MODERATE_UPLOADS:
            self.object.is_approved = False
        if settings.RESOURCE_PUBLISHING:
            self.object.is_published = False
        self.object.save()
        form.save_many2many()
        self.object.set_permissions(form.cleaned_data['permissions'])

        abstract = None
        date = None
        regions = []
        keywords = []
        bbox = None

        out = {'success': False}

        if abstract:
            self.object.abstract = abstract

        if date:
            self.object.date = date
            self.object.date_type = "Creation"

        if len(regions) > 0:
            self.object.regions.add(*regions)

        if len(keywords) > 0:
            self.object.keywords.add(*keywords)

        if bbox:
            bbox_x0, bbox_x1, bbox_y0, bbox_y1 = bbox
            Document.objects.filter(id=self.object.pk).update(
                bbox_x0=bbox_x0,
                bbox_x1=bbox_x1,
                bbox_y0=bbox_y0,
                bbox_y1=bbox_y1)

        self.object.save(notify=True)
        # register_event(self.request, EventType.EVENT_UPLOAD, self.object)

        if self.request.GET.get('no__redirect', False):
            out['success'] = True
            out['url'] = reverse(
                'document_detail',
                args=(
                    self.object.id,
                ))
            if out['success']:
                status_code = 200
            else:
                status_code = 400
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=status_code)
        else:
            return HttpResponseRedirect(
                reverse(
                    'document_metadata',
                    args=(
                        self.object.id,
                    )))


class BimsDocumentUpdateView(UpdateView):
    model = BimsDocument
    fields = ['year']
    template_name = 'documents/bims_document_update.html'

    def get_success_url(self):
        return reverse(
            'document_detail',
            args=(
                self.object.document.id,
            ))

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        pk = self.kwargs.get(self.pk_url_kwarg)
        try:
            obj = queryset.get(document__id=pk)
        except BimsDocument.DoesNotExist:
            obj = BimsDocument.objects.create(
                document=Document.objects.get(id=pk)
            )
        return obj

    def form_valid(self, form):
        post_dict = self.request.POST.dict()
        year = self.request.POST.get('year', None)
        title = self.request.POST.get('document_title', None)
        self.object.year = year
        self.object.authors.clear()
        if title:
            doc = self.object.document
            doc.title = title
            doc.save()
        for key in post_dict:
            if 'author' in key:
                user_string = post_dict[key].strip()
                first_name = user_string.split(' ')[0]
                last_name = ' '.join(user_string.split(' ')[1:])
                user = get_user_from_name(
                    first_name=first_name,
                    last_name=last_name
                )
                if user:
                    self.object.authors.add(user)
        self.object.save()
        return super(BimsDocumentUpdateView, self).form_valid(
            form
        )


class BimsDocumentUploadView(DocumentUploadView):
    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        # by default, if RESOURCE_PUBLISHING=True then document.is_published
        # must be set to False
        # RESOURCE_PUBLISHING works in similar way as ADMIN_MODERATE_UPLOADS,
        # but is applied to documents only. ADMIN_MODERATE_UPLOADS has wider
        # usage
        is_published = not (
                settings.RESOURCE_PUBLISHING or
                settings.ADMIN_MODERATE_UPLOADS)
        self.object.is_published = is_published
        self.object.save()

        return super(BimsDocumentUploadView, self).form_valid(
                form
        )


class SourceReferenceBimsDocumentUploadView(DocumentUploadView):
    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        # by default, if RESOURCE_PUBLISHING=True then document.is_published
        # must be set to False
        # RESOURCE_PUBLISHING works in similar way as ADMIN_MODERATE_UPLOADS,
        # but is applied to documents only. ADMIN_MODERATE_UPLOADS has wider
        # usage
        is_published = not (
                settings.RESOURCE_PUBLISHING or
                settings.ADMIN_MODERATE_UPLOADS)
        self.object.is_published = is_published

        # save abstract
        try:
            self.object.abstract = form.data['description']
        except KeyError:
            pass

        # Save document source
        try:
            self.object.supplemental_information = json.dumps({
                'document_source': form.data['document_source']
            })
        except KeyError:
            pass

        self.object.save()
        super(SourceReferenceBimsDocumentUploadView, self).form_valid(
            form
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
            except Exception:
                pass
        if keyword:
            TaggedContentItem.objects.get_or_create(
                content_object=self.object, tag=keyword)

        # add additional metadata
        bims_document, created = BimsDocument.objects.get_or_create(
            document=self.object)
        bims_document.update_metadata(form.data)

        # Update authors
        try:
            authors = form.data['author']
            authors = create_users_from_string(authors)
            if authors:
                bims_document.authors.clear()
                for author in authors:
                    bims_document.authors.add(author)
        except KeyError:
            pass

        return HttpResponse(
            json.dumps({
                'id': self.object.id,
                'title': self.object.title,
                'author': self.object.bimsdocument.authors_string,
                'year': self.object.bimsdocument.year
            }),
            content_type='application/json',
            status=200)
