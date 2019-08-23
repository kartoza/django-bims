import json
import logging
from itertools import chain

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.forms.utils import ErrorList

from geonode.utils import resolve_object
from geonode.people.forms import ProfileForm
from geonode.base.forms import CategoryForm
from geonode.base.models import (
    TopicCategory, HierarchicalKeyword, TaggedContentItem
)
from geonode.documents.models import Document
from geonode.documents.forms import DocumentForm
from geonode.groups.models import GroupProfile
from geonode.documents.views import DocumentUploadView

from bims.models.bims_document import BimsDocument
from bims.models.taxon import Taxon

logger = logging.getLogger("geonode.documents.views")

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this document")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this document.")
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this document")
_PERMISSION_MSG_METADATA = _(
        "You are not permitted to modify this document's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this document")


def _resolve_document(request, docid, permission='base.change_resourcebase',
                      msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the document by the provided primary key
    and check the optional permission.
    '''
    return resolve_object(request, Document, {'pk': docid},
                          permission=permission, permission_msg=msg, **kwargs)


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
        if self.request.method == 'POST' and self.object:
            taxon_links = self.request.POST.get('taxon-links', None)
            if taxon_links:
                taxon_links = taxon_links.split(',')
                for taxon_link in taxon_links:
                    try:
                        taxon = Taxon.objects.get(
                                id=taxon_link
                        )
                        taxon.documents.add(
                                self.object
                        )
                        taxon.save()
                    except Taxon.DoesNotExist as e:  # noqa
                        pass

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

        return HttpResponse(
            json.dumps({
                'id': self.object.id,
                'title': self.object.title
            }),
            content_type='application/json',
            status=200)


@login_required
def document_metadata(
        request,
        docid,
        template='documents/document_metadata.html',
        ajax=True):
    document = None
    try:
        document = _resolve_document(
                request,
                docid,
                'base.change_resourcebase_metadata',
                _PERMISSION_MSG_METADATA)

    except Http404:
        return HttpResponse(
                loader.render_to_string(
                        '404.html', context={
                        }, request=request), status=404)

    except PermissionDenied:
        return HttpResponse(
                loader.render_to_string(
                        '401.html', context={
                            'error_message': _(
                                "You are not allowed to edit this document.")
                        }, request=request), status=403)

    if document is None:
        return HttpResponse(
                'An unknown error has occured.',
                content_type="text/plain",
                status=401
        )

    else:
        poc = document.poc
        metadata_author = document.metadata_author
        topic_category = document.category

        if request.method == "POST":
            document_form = DocumentForm(
                    request.POST,
                    instance=document,
                    prefix="resource")
            category_form = CategoryForm(request.POST,
                                         prefix="category_choice_field",
                                         initial=int(
                                                 request.POST[
                                                     "category_choice_field"])
                                         if "category_choice_field" in
                                            request.POST else None)
        else:
            document_form = DocumentForm(instance=document, prefix="resource")
            category_form = CategoryForm(
                    prefix="category_choice_field",
                    initial=topic_category.id if topic_category else None)

        if request.method == "POST" and document_form.is_valid(
        ) and category_form.is_valid():
            new_poc = document_form.cleaned_data['poc']
            new_author = document_form.cleaned_data['metadata_author']
            new_keywords = document_form.cleaned_data['keywords']
            new_regions = document_form.cleaned_data['regions']
            new_category = TopicCategory.objects.get(
                    id=category_form.cleaned_data['category_choice_field'])

            if new_poc is None:
                if poc is None:
                    poc_form = ProfileForm(
                            request.POST,
                            prefix="poc",
                            instance=poc)
                else:
                    poc_form = ProfileForm(request.POST, prefix="poc")
                if poc_form.is_valid():
                    if len(poc_form.cleaned_data['profile']) == 0:
                        # FIXME use form.add_error in django > 1.7
                        errors = poc_form._errors.setdefault(
                                'profile', ErrorList())
                        errors.append(
                                _(
                                    'You must set a point of '
                                    'contact for this resource'))
                        poc = None
                if poc_form.has_changed and poc_form.is_valid():
                    new_poc = poc_form.save()

            if new_author is None:
                if metadata_author is None:
                    author_form = ProfileForm(request.POST, prefix="author",
                                              instance=metadata_author)
                else:
                    author_form = ProfileForm(request.POST, prefix="author")
                if author_form.is_valid():
                    if len(author_form.cleaned_data['profile']) == 0:
                        # FIXME use form.add_error in django > 1.7
                        errors = author_form._errors.setdefault(
                                'profile', ErrorList())
                        errors.append(
                                _('You must set an author for this resource'))
                        metadata_author = None
                if author_form.has_changed and author_form.is_valid():
                    new_author = author_form.save()

            the_document = document_form.instance
            if new_poc is not None and new_author is not None:
                the_document.poc = new_poc
                the_document.metadata_author = new_author
            if new_keywords:
                the_document.keywords.clear()
                the_document.keywords.add(*new_keywords)
            if new_regions:
                the_document.regions.clear()
                the_document.regions.add(*new_regions)
            the_document.save()
            document_form.save_many2many()
            Document.objects.filter(
                    id=the_document.id).update(
                    category=new_category)

            # Update taxon links
            doc = Document.objects.get(
                    id=the_document.id
            )
            taxon_links = request.POST.get('taxon-links', None)
            old_taxon_links = Taxon.objects.filter(
                    documents__id=the_document.id
            )
            for taxon_link in old_taxon_links:
                taxon_link.documents.remove(
                        doc
                )
            if taxon_links:
                taxon_links = taxon_links.split(',')
                for taxon_link in taxon_links:
                    try:
                        taxon = Taxon.objects.get(
                                id=taxon_link
                        )
                        taxon.documents.add(
                                doc
                        )
                        taxon.save()
                    except Taxon.DoesNotExist as e:  # noqa
                        pass

            if getattr(settings, 'SLACK_ENABLED', False):
                try:
                    from geonode.contrib.slack.utils import \
                        build_slack_message_document, send_slack_messages
                    send_slack_messages(
                            build_slack_message_document(
                                    "document_edit", the_document))
                except BaseException:
                    print("Could not send slack "
                          "message for modified document.")

            if not ajax:
                return HttpResponseRedirect(
                        reverse(
                                'document_detail',
                                args=(
                                    document.id,
                                )))

            message = document.id

            return HttpResponse(json.dumps({'message': message}))

        # - POST Request Ends here -

        # Request.GET
        if poc is not None:
            document_form.fields['poc'].initial = poc.id
            poc_form = ProfileForm(prefix="poc")
            poc_form.hidden = True

        if metadata_author is not None:
            document_form.fields[
                'metadata_author'].initial = metadata_author.id
            author_form = ProfileForm(prefix="author")
            author_form.hidden = True

        metadata_author_groups = []
        if request.user.is_superuser or request.user.is_staff:
            metadata_author_groups = GroupProfile.objects.all()
        else:
            try:
                all_metadata_author_groups = chain(
                        request.user.group_list_all(),
                        GroupProfile.objects.exclude(access="private").exclude(
                            access="public-invite"))
            except BaseException:
                all_metadata_author_groups = GroupProfile.objects.exclude(
                        access="private").exclude(access="public-invite")
            [metadata_author_groups.append(item) for item in
             all_metadata_author_groups
             if item not in metadata_author_groups]

        if settings.ADMIN_MODERATE_UPLOADS:
            if not request.user.is_superuser:
                document_form.fields['is_published'].widget.attrs.update(
                        {'disabled': 'true'})

                can_change_metadata = request.user.has_perm(
                        'change_resourcebase_metadata',
                        document.get_self_resource())
                try:
                    is_manager = request.user.groupmember_set.all().filter(
                        role='manager').exists()
                except BaseException:
                    is_manager = False
                if not is_manager or not can_change_metadata:
                    document_form.fields['is_approved'].widget.attrs.update(
                            {'disabled': 'true'})

        return render(request, template, context={
            "resource": document,
            "document": document,
            "document_form": document_form,
            "poc_form": poc_form,
            "author_form": author_form,
            "category_form": category_form,
            "metadata_author_groups": metadata_author_groups,
            "GROUP_MANDATORY_RESOURCES": getattr(settings,
                                                 'GROUP_MANDATORY_RESOURCES',
                                                 False),
        })
