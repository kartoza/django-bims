import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
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
from geonode.documents.models import Document
from bims.views.mixin.session_form import SessionFormMixin
from bims.views.mixin.session_form.exception import (
    SessionDataNotFound,
    SessionNotFound,
    SessionUUIDNotFound
)

logger = logging.getLogger('bims')


class SourceReferenceView(TemplateView, SessionFormMixin):
    """ View for source references form """
    session_identifier = 'fish-form'
    template_name = 'source_references/source_reference_page.html'
    additional_context = {}
    SOURCE_REFERENCE_CATEGORIES = {

    }

    def get_context_data(self, **kwargs):
        context = super(SourceReferenceView, self).get_context_data(**kwargs)
        context.update(self.additional_context)
        context.update({
            'documents': Document.objects.all(),
            'database': DatabaseRecord.objects.all(),
            'ALLOWED_DOC_TYPES': ','.join(
                ['.%s' % type for type in settings.ALLOWED_DOCUMENT_TYPES])
        })
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        try:
            self.additional_context = self.get_session_data(self.request)
        except (SessionNotFound, SessionDataNotFound) as e:
            return HttpResponseBadRequest('%s' % e)
        except SessionUUIDNotFound:
            self.additional_context = {
                'sessions': self.get_last_session(self.request)
            }
        return super(SourceReferenceView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        category = None
        try:
            session_data = self.get_session_data(self.request)
            data = request.POST.dict()
            try:
                records = session_data['records']
                biological_records = BiologicalCollectionRecord.objects. \
                    filter(id__in=records)
            except KeyError:
                return HttpResponseBadRequest('Session is broken')
            category = data['reference_category']

            # create source reference
            source = None
            if category != 'no-source':
                source = int(data[category + '-id'])
            else:
                category = None
            source_reference = SourceReference.create_source_reference(
                category, source, data['note'])
            biological_records.update(source_reference=source_reference)

            # delete the session
            session_uuid = self.request.GET.get('session', None)
            self.remove_session(request, session_uuid)
        except (
                SessionNotFound,
                SessionDataNotFound,
                SessionUUIDNotFound,
                CategoryIsNotRecognized,
                SourceIsNotFound) as e:
            return HttpResponseBadRequest('%s' % e)
        except KeyError as e:
            return HttpResponseBadRequest('%s is not in data' % e)
        except ValueError:
            return HttpResponseBadRequest(
                '%s is not integer' % (category + '-id'))
        return HttpResponseRedirect(reverse('nonvalidated-user-list'))
