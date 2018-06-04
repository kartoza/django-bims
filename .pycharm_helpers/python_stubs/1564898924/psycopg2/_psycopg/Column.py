# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .tuple import tuple

class Column(tuple):
    """ Column(name, type_code, display_size, internal_size, precision, scale, null_ok) """
    def _asdict(self): # reliably restored by inspect
        """ Return a new OrderedDict which maps field names to their values. """
        pass

    @classmethod
    def _make(cls, *args, **kwargs): # real signature unknown
        """ Make a new Column object from a sequence or iterable """
        pass

    def _replace(_self, **kwds): # reliably restored by inspect
        """ Return a new Column object replacing specified fields with new values """
        pass

    def __getnewargs__(self): # reliably restored by inspect
        """ Return self as a plain tuple.  Used by copy and pickle. """
        pass

    def __init__(self, name, type_code, display_size, internal_size, precision, scale, null_ok): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(_cls, name, type_code, display_size, internal_size, precision, scale, null_ok): # reliably restored by inspect
        """ Create new instance of Column(name, type_code, display_size, internal_size, precision, scale, null_ok) """
        pass

    def __repr__(self): # reliably restored by inspect
        """ Return a nicely formatted representation string """
        pass

    display_size = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Alias for field number 2"""

    internal_size = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Alias for field number 3"""

    name = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Alias for field number 0"""

    null_ok = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Alias for field number 6"""

    precision = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Alias for field number 4"""

    scale = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Alias for field number 5"""

    type_code = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Alias for field number 1"""


    _fields = (
        'name',
        'type_code',
        'display_size',
        'internal_size',
        'precision',
        'scale',
        'null_ok',
    )
    _source = "from builtins import property as _property, tuple as _tuple\nfrom operator import itemgetter as _itemgetter\nfrom collections import OrderedDict\n\nclass Column(tuple):\n    'Column(name, type_code, display_size, internal_size, precision, scale, null_ok)'\n\n    __slots__ = ()\n\n    _fields = ('name', 'type_code', 'display_size', 'internal_size', 'precision', 'scale', 'null_ok')\n\n    def __new__(_cls, name, type_code, display_size, internal_size, precision, scale, null_ok):\n        'Create new instance of Column(name, type_code, display_size, internal_size, precision, scale, null_ok)'\n        return _tuple.__new__(_cls, (name, type_code, display_size, internal_size, precision, scale, null_ok))\n\n    @classmethod\n    def _make(cls, iterable, new=tuple.__new__, len=len):\n        'Make a new Column object from a sequence or iterable'\n        result = new(cls, iterable)\n        if len(result) != 7:\n            raise TypeError('Expected 7 arguments, got %d' % len(result))\n        return result\n\n    def _replace(_self, **kwds):\n        'Return a new Column object replacing specified fields with new values'\n        result = _self._make(map(kwds.pop, ('name', 'type_code', 'display_size', 'internal_size', 'precision', 'scale', 'null_ok'), _self))\n        if kwds:\n            raise ValueError('Got unexpected field names: %r' % list(kwds))\n        return result\n\n    def __repr__(self):\n        'Return a nicely formatted representation string'\n        return self.__class__.__name__ + '(name=%r, type_code=%r, display_size=%r, internal_size=%r, precision=%r, scale=%r, null_ok=%r)' % self\n\n    def _asdict(self):\n        'Return a new OrderedDict which maps field names to their values.'\n        return OrderedDict(zip(self._fields, self))\n\n    def __getnewargs__(self):\n        'Return self as a plain tuple.  Used by copy and pickle.'\n        return tuple(self)\n\n    name = _property(_itemgetter(0), doc='Alias for field number 0')\n\n    type_code = _property(_itemgetter(1), doc='Alias for field number 1')\n\n    display_size = _property(_itemgetter(2), doc='Alias for field number 2')\n\n    internal_size = _property(_itemgetter(3), doc='Alias for field number 3')\n\n    precision = _property(_itemgetter(4), doc='Alias for field number 4')\n\n    scale = _property(_itemgetter(5), doc='Alias for field number 5')\n\n    null_ok = _property(_itemgetter(6), doc='Alias for field number 6')\n\n"
    __slots__ = ()


