import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.urls import reverse
from django.http import HttpResponseRedirect
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.source_reference import (
    DatabaseRecord,
    SourceReference,
    CategoryIsNotRecognized,
    SourceIsNotFound
)
from geonode.base.models import HierarchicalKeyword
from geonode.documents.models import Document
from bims.views.mixin.session_form import SessionFormMixin
from bims.views.mixin.session_form.exception import (
    SessionDataNotFound,
    SessionNotFound,
    SessionUUIDNotFound
)
from bims.serializers.database_record import DatabaseRecordSerializer

logger = logging.getLogger('bims')


class SourceReferenceView(TemplateView, SessionFormMixin):
    """ View for source references form """
    session_identifier = 'fish-form'
    template_name = 'source_references/source_reference_page.html'
    additional_context = {}
    collection_record = None

    def get_context_data(self, **kwargs):
        context = super(SourceReferenceView, self).get_context_data(**kwargs)
        context.update(self.additional_context)
        additional_context_data = {}

        source_reference_document = []
        try:
            keyword = HierarchicalKeyword.objects.get(
                slug='bims_source_reference')
            source_reference_document = Document.objects.filter(
                keywords=keyword)
        except HierarchicalKeyword.DoesNotExist:
            pass

        if 'records' in context:
            # check if there is existing source_reference from collection
            collection_records = BiologicalCollectionRecord.objects.filter(
                id__in=context['records'],
                source_reference__isnull=False
            ).distinct('source_reference')
            if collection_records.exists():
                if collection_records.count() > 1:
                    # There are multiple source references, skip
                    pass
                else:
                    self.collection_record = collection_records[0]

        if self.collection_record:
            if self.collection_record.source_reference:
                additional_context_data['reference_category'] = (
                    self.collection_record.source_reference.reference_type
                )
                additional_context_data['source_reference'] = (
                    self.collection_record.source_reference.source
                )
                additional_context_data['note'] = (
                    self.collection_record.source_reference.note
                )
        context.update({
            'documents': source_reference_document,
            'database': DatabaseRecordSerializer(
                DatabaseRecord.objects.all(), many=True).data,
            'ALLOWED_DOC_TYPES': ','.join(
                ['.%s' % type for type in settings.ALLOWED_DOCUMENT_TYPES]),
            'additional_context_data': additional_context_data
        })
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        collection_id = self.request.GET.get('collection_id', None)
        identifier = self.request.GET.get('identifier', None)
        if identifier:
            self.session_identifier = identifier
        session_found, session_not_found_message = True, ''
        try:
            self.additional_context = self.get_session_data(self.request)
        except (SessionNotFound, SessionDataNotFound) as e:
            session_found, session_not_found_message = False, e
        except SessionUUIDNotFound:
            self.additional_context = {
                'sessions': self.get_last_session(self.request)
            }
        if not session_found and not collection_id:
            return HttpResponseBadRequest('%s' % session_not_found_message)
        elif collection_id:
            self.collection_record = get_object_or_404(
                BiologicalCollectionRecord,
                pk=collection_id,
            )
        return super(SourceReferenceView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        collection_id = self.request.GET.get('collection_id', None)
        identifier = self.request.GET.get('identifier', None)
        if identifier:
            self.session_identifier = identifier
        session_found, session_not_found_message = True, ''
        category = None
        data = request.POST.dict()
        biological_records = None

        try:
            category = data['reference_category']
            if category == 'no-source':
                note = data['note']
                if note == '':
                    return HttpResponseBadRequest('Note is empty')
            session_data = self.get_session_data(self.request)
            try:
                records = session_data['records']
                biological_records = BiologicalCollectionRecord.objects. \
                    filter(id__in=records)
            except KeyError:
                return HttpResponseBadRequest('Session is broken')
            # delete the session
            session_uuid = self.request.GET.get('session', None)
            self.remove_session(request, session_uuid)
        except (
                SessionNotFound,
                SessionDataNotFound,
                SessionUUIDNotFound) as e:
            session_found, session_not_found_message = False, e
        except KeyError as e:
            return HttpResponseBadRequest('%s is not in data' % e)
        except ValueError:
            return HttpResponseBadRequest(
                '%s is not integer' % (category + '-id'))

        if not session_found and not collection_id:
            return HttpResponseBadRequest('%s' % session_not_found_message)
        elif collection_id:
            collection_record = get_object_or_404(
                BiologicalCollectionRecord,
                pk=collection_id,
            )
            biological_records = BiologicalCollectionRecord.objects.filter(
                id__in=[collection_record.id]
            )

        # create source reference
        try:
            source = None
            if category != 'no-source':
                source = int(data[category + '-id'])
            else:
                category = None
            source_reference = SourceReference.create_source_reference(
                category, source, data.get('note', None))
        except SourceIsNotFound as e:
            return HttpResponseBadRequest('%s' % e)
        except CategoryIsNotRecognized as e:
            return HttpResponseBadRequest('%s' % e)

        if biological_records:
            biological_records.update(source_reference=source_reference)

        response_redirect = reverse('nonvalidated-user-list')
        if request.GET.get('next', None):
            response_redirect = request.GET.get('next')
        return HttpResponseRedirect(response_redirect)
