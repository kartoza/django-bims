# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .object import object

class ISQLQuote(object):
    """
    Abstract ISQLQuote protocol
    
    An object conform to this protocol should expose a ``getquoted()`` method
    returning the SQL representation of the object.
    """
    def getbinary(self): # real signature unknown; restored from __doc__
        """ getbinary() -- return SQL-quoted binary representation of this object """
        pass

    def getbuffer(self): # real signature unknown; restored from __doc__
        """ getbuffer() -- return this object """
        pass

    def getquoted(self): # real signature unknown; restored from __doc__
        """ getquoted() -- return SQL-quoted representation of this object """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    _wrapped = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default



