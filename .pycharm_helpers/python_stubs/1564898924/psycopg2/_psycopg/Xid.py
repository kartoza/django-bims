# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .object import object

class Xid(object):
    """
    A transaction identifier used for two-phase commit.
    
    Usually returned by the connection methods `~connection.xid()` and
    `~connection.tpc_recover()`.
    `!Xid` instances can be unpacked as a 3-item tuples containing the items
    :samp:`({format_id},{gtrid},{bqual})`.
    The `!str()` of the object returns the *transaction ID* used
    in the commands sent to the server.
    
    See :ref:`tpc` for an introduction.
    """
    def from_string(self, *args, **kwargs): # real signature unknown
        """
        Create a `!Xid` object from a string representation. Static method.
        
        If *s* is a PostgreSQL transaction ID produced by a XA transaction,
        the returned object will have `format_id`, `gtrid`, `bqual` set to
        the values of the preparing XA id.
        Otherwise only the `!gtrid` is populated with the unparsed string.
        The operation is the inverse of the one performed by `!str(xid)`.
        """
        pass

    def __getitem__(self, *args, **kwargs): # real signature unknown
        """ Return self[key]. """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __len__(self, *args, **kwargs): # real signature unknown
        """ Return len(self). """
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    def __str__(self, *args, **kwargs): # real signature unknown
        """ Return str(self). """
        pass

    bqual = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Branch qualifier of the transaction.

In a XA transaction every resource participating to a transaction
receives a distinct branch qualifier.
`!None` if the transaction doesn't follow the XA standard."""

    database = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Database the recovered transaction belongs to."""

    format_id = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Format ID in a XA transaction.

A non-negative 32 bit integer.
`!None` if the transaction doesn't follow the XA standard."""

    gtrid = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Global transaction ID in a XA transaction.

If the transaction doesn't follow the XA standard, it is the plain
*transaction ID* used in the server commands."""

    owner = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Name of the user who prepared a recovered transaction."""

    prepared = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Timestamp (with timezone) in which a recovered transaction was prepared."""



