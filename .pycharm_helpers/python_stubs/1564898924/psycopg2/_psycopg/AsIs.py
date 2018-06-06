# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .object import object

class AsIs(object):
    """ AsIs(str) -> new AsIs adapter object """
    def getquoted(self): # real signature unknown; restored from __doc__
        """ getquoted() -> wrapped object value as SQL-quoted string """
        pass

    def __conform__(self, *args, **kwargs): # real signature unknown
        pass

    def __init__(self, p_str): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __str__(self, *args, **kwargs): # real signature unknown
        """ Return str(self). """
        pass

    adapted = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default



