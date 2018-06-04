# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .object import object

class ReplicationMessage(object):
    """ A replication protocol message. """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    cursor = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Related ReplcationCursor object."""

    data_size = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Raw size of the message data in bytes."""

    data_start = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """LSN position of the start of this message."""

    payload = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The actual message data."""

    send_time = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """send_time - Timestamp of the replication message departure from the server."""

    wal_end = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """LSN position of the current end of WAL on the server."""



