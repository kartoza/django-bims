# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .object import object

class lobject(object):
    """ A database large object. """
    def close(self): # real signature unknown; restored from __doc__
        """ close() -- Close the lobject. """
        pass

    def export(self, filename): # real signature unknown; restored from __doc__
        """ export(filename) -- Export large object to given file. """
        pass

    def read(self, size=-1): # real signature unknown; restored from __doc__
        """ read(size=-1) -- Read at most size bytes or to the end of the large object. """
        pass

    def seek(self, offset, whence=0): # real signature unknown; restored from __doc__
        """ seek(offset, whence=0) -- Set the lobject's current position. """
        pass

    def tell(self): # real signature unknown; restored from __doc__
        """ tell() -- Return the lobject's current position. """
        pass

    def truncate(self, len=0): # real signature unknown; restored from __doc__
        """ truncate(len=0) -- Truncate large object to given size. """
        pass

    def unlink(self): # real signature unknown; restored from __doc__
        """ unlink() -- Close and then remove the lobject. """
        pass

    def write(self, p_str): # real signature unknown; restored from __doc__
        """ write(str) -- Write a string to the large object. """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
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

    closed = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The if the large object is closed (no file-like methods)."""

    mode = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Open mode."""

    oid = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The backend OID associated to this lobject."""



