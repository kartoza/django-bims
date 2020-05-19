from .exception import (
    SessionNotFound,
    SessionUUIDNotFound,
    SessionDataNotFound
)


class SessionFormMixin(object):
    session_identifier = ''

    def get_last_session(self, request):
        try:
            return request.session[self.session_identifier]
        except KeyError:
            return None

    def add_last_session(self, request, session_uuid, data):
        try:
            session_data = request.session[self.session_identifier]
        except KeyError:
            session_data = {}
        session_data[session_uuid] = data
        request.session[self.session_identifier] = session_data

    def remove_session(self, request, session_uuid):
        try:
            session_data = request.session[self.session_identifier]
            del session_data[session_uuid]
            request.session[self.session_identifier] = session_data
        except KeyError:
            pass

    def get_session_data(self, request):
        session = self.get_last_session(request)
        if not session:
            raise SessionNotFound()
        try:
            session_uuid = request.GET.get('session', None)
            if not session_uuid:
                raise SessionUUIDNotFound()
            return session[session_uuid]
        except KeyError:
            raise SessionDataNotFound()
