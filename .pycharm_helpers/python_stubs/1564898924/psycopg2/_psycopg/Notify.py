# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .object import object

class Notify(object):
    """
    A notification received from the backend.
    
    `!Notify` instances are made available upon reception on the
    `~connection.notifies` member of the listening connection. The object
    can be also accessed as a 2 items tuple returning the members
    :samp:`({pid},{channel})` for backward compatibility.
    
    See :ref:`async-notify` for details.
    """
    def __eq__(self, *args, **kwargs): # real signature unknown
        """ Return self==value. """
        pass

    def __getitem__(self, *args, **kwargs): # real signature unknown
        """ Return self[key]. """
        pass

    def __ge__(self, *args, **kwargs): # real signature unknown
        """ Return self>=value. """
        pass

    def __gt__(self, *args, **kwargs): # real signature unknown
        """ Return self>value. """
        pass

    def __hash__(self, *args, **kwargs): # real signature unknown
        """ Return hash(self). """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __len__(self, *args, **kwargs): # real signature unknown
        """ Return len(self). """
        pass

    def __le__(self, *args, **kwargs): # real signature unknown
        """ Return self<=value. """
        pass

    def __lt__(self, *args, **kwargs): # real signature unknown
        """ Return self<value. """
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __ne__(self, *args, **kwargs): # real signature unknown
        """ Return self!=value. """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    channel = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The name of the channel to which the notification was sent."""

    payload = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The payload message of the notification.

Attaching a payload to a notification is only available since
PostgreSQL 9.0: for notifications received from previous versions
of the server this member is always the empty string."""

    pid = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The ID of the backend process that sent the notification.

Note: if the sending session was handled by Psycopg, you can use
`~connection.get_backend_pid()` to know its PID."""



