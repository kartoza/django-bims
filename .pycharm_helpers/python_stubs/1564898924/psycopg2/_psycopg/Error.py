# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .Exception import Exception

class Error(Exception):
    """ Base class for error exceptions. """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __reduce__(self, *args, **kwargs): # real signature unknown
        pass

    def __setstate__(self, *args, **kwargs): # real signature unknown
        pass

    cursor = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The cursor that raised the exception, if available, else None"""

    diag = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """A Diagnostics object to get further information about the error"""

    pgcode = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The error code returned by the backend, if available, else None"""

    pgerror = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The error message returned by the backend, if available, else None"""



