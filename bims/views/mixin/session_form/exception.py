class SessionUUIDNotFound(Exception):
    """ Exception if no session uuid found"""

    def __init__(self):
        message = 'You don\'t have any session'
        errors = message
        super(SessionUUIDNotFound, self).__init__(message)
        self.errors = errors


class SessionNotFound(Exception):
    """ Exception if no session found"""

    def __init__(self):
        message = 'You don\'t have any session'
        errors = message
        super(SessionNotFound, self).__init__(message)
        self.errors = errors


class SessionDataNotFound(Exception):
    """ Exception if session data is not found"""

    def __init__(self):
        message = 'Session is wrong or expired'
        errors = message
        super(SessionDataNotFound, self).__init__(message)
        self.errors = errors
