import logging
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.urls import reverse
from django.http import HttpResponseRedirect
from bims.views.fish_form import FishFormView
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.source_reference import (
    DatabaseRecord,
    SourceReference,
    CategoryIsNotRecognized,
    SourceIsNotFound
)
from geonode.documents.models import Document

logger = logging.getLogger('bims')


class SessionUUIDNotFound(Exception):
    """ Exception if no session uuid found"""

    def __init__(self):
        message = 'you don\'t have any session'
        errors = message
        super(SessionUUIDNotFound, self).__init__(message)
        self.errors = errors


class SessionNotFound(Exception):
    """ Exception if no session found"""

    def __init__(self):
        message = 'you don\'t have any session'
        errors = message
        super(SessionNotFound, self).__init__(message)
        self.errors = errors


class SessionDataNotFound(Exception):
    """ Exception if session data is not found"""

    def __init__(self):
        message = 'session is wrong or expired'
        errors = message
        super(SessionDataNotFound, self).__init__(message)
        self.errors = errors


class SourceReferenceView(TemplateView):
    """ View for source references form """
    template_name = 'source_references/source_reference_page.html'
    additional_context = {}
    SOURCE_REFERENCE_CATEGORIES = {

    }

    def get_context_data(self, **kwargs):
        context = super(SourceReferenceView, self).get_context_data(**kwargs)
        context.update(self.additional_context)
        context.update({
            'documents': Document.objects.all(),
            'database': DatabaseRecord.objects.all()
        })
        return context

    def check_session_data(self):
        session = FishFormView.get_last_session(self.request)
        if not session:
            raise SessionNotFound()
        try:
            session_uuid = self.request.GET.get('session', None)
            if not session_uuid:
                raise SessionUUIDNotFound()
            return session[session_uuid]
        except KeyError:
            raise SessionDataNotFound()

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        try:
            self.additional_context = self.check_session_data()
        except (SessionNotFound, SessionDataNotFound) as e:
            return HttpResponseBadRequest('%s' % e)
        except SessionUUIDNotFound:
            self.additional_context = {
                'sessions': FishFormView.get_last_session(self.request)
            }
        return super(SourceReferenceView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        category = None
        try:
            session_data = self.check_session_data()
            data = request.POST.dict()
            try:
                records = session_data['records']
                biological_records = BiologicalCollectionRecord.objects. \
                    filter(id__in=records)
            except KeyError:
                return HttpResponseBadRequest('session is broken')
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
            FishFormView.remove_session(request, session_uuid)
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
