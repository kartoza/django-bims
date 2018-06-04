# encoding: utf-8
# module _operator
# from (built-in)
# by generator 1.145
"""
Operator interface.

This module exports a set of functions implemented in C corresponding
to the intrinsic operators of Python.  For example, operator.add(x, y)
is equivalent to the expression x+y.  The function names are those
used for special methods; variants without leading and trailing
'__' are also provided for convenience.
"""
# no imports

# functions

def abs(a): # real signature unknown; restored from __doc__
    """ abs(a) -- Same as abs(a). """
    pass

def add(a, b): # real signature unknown; restored from __doc__
    """ add(a, b) -- Same as a + b. """
    pass

def and_(a, b): # real signature unknown; restored from __doc__
    """ and_(a, b) -- Same as a & b. """
    pass

def concat(a, b): # real signature unknown; restored from __doc__
    """ concat(a, b) -- Same as a + b, for a and b sequences. """
    pass

def contains(a, b): # real signature unknown; restored from __doc__
    """ contains(a, b) -- Same as b in a (note reversed operands). """
    pass

def countOf(a, b): # real signature unknown; restored from __doc__
    """ countOf(a, b) -- Return the number of times b occurs in a. """
    pass

def delitem(a, b): # real signature unknown; restored from __doc__
    """ delitem(a, b) -- Same as del a[b]. """
    pass

def eq(a, b): # real signature unknown; restored from __doc__
    """ eq(a, b) -- Same as a==b. """
    pass

def floordiv(a, b): # real signature unknown; restored from __doc__
    """ floordiv(a, b) -- Same as a // b. """
    pass

def ge(a, b): # real signature unknown; restored from __doc__
    """ ge(a, b) -- Same as a>=b. """
    pass

def getitem(a, b): # real signature unknown; restored from __doc__
    """ getitem(a, b) -- Same as a[b]. """
    pass

def gt(a, b): # real signature unknown; restored from __doc__
    """ gt(a, b) -- Same as a>b. """
    pass

def iadd(a, b): # real signature unknown; restored from __doc__
    """ a = iadd(a, b) -- Same as a += b. """
    pass

def iand(a, b): # real signature unknown; restored from __doc__
    """ a = iand(a, b) -- Same as a &= b. """
    pass

def iconcat(a, b): # real signature unknown; restored from __doc__
    """ a = iconcat(a, b) -- Same as a += b, for a and b sequences. """
    pass

def ifloordiv(a, b): # real signature unknown; restored from __doc__
    """ a = ifloordiv(a, b) -- Same as a //= b. """
    pass

def ilshift(a, b): # real signature unknown; restored from __doc__
    """ a = ilshift(a, b) -- Same as a <<= b. """
    pass

def imatmul(a, b): # real signature unknown; restored from __doc__
    """ a = imatmul(a, b) -- Same as a @= b. """
    pass

def imod(a, b): # real signature unknown; restored from __doc__
    """ a = imod(a, b) -- Same as a %= b. """
    pass

def imul(a, b): # real signature unknown; restored from __doc__
    """ a = imul(a, b) -- Same as a *= b. """
    pass

def index(a): # real signature unknown; restored from __doc__
    """ index(a) -- Same as a.__index__() """
    pass

def indexOf(a, b): # real signature unknown; restored from __doc__
    """ indexOf(a, b) -- Return the first index of b in a. """
    pass

def inv(a): # real signature unknown; restored from __doc__
    """ inv(a) -- Same as ~a. """
    pass

def invert(a): # real signature unknown; restored from __doc__
    """ invert(a) -- Same as ~a. """
    pass

def ior(a, b): # real signature unknown; restored from __doc__
    """ a = ior(a, b) -- Same as a |= b. """
    pass

def ipow(a, b): # real signature unknown; restored from __doc__
    """ a = ipow(a, b) -- Same as a **= b. """
    pass

def irshift(a, b): # real signature unknown; restored from __doc__
    """ a = irshift(a, b) -- Same as a >>= b. """
    pass

def isub(a, b): # real signature unknown; restored from __doc__
    """ a = isub(a, b) -- Same as a -= b. """
    pass

def is_(a, b): # real signature unknown; restored from __doc__
    """ is_(a, b) -- Same as a is b. """
    pass

def is_not(a, b): # real signature unknown; restored from __doc__
    """ is_not(a, b) -- Same as a is not b. """
    pass

def itruediv(a, b): # real signature unknown; restored from __doc__
    """ a = itruediv(a, b) -- Same as a /= b """
    pass

def ixor(a, b): # real signature unknown; restored from __doc__
    """ a = ixor(a, b) -- Same as a ^= b. """
    pass

def le(a, b): # real signature unknown; restored from __doc__
    """ le(a, b) -- Same as a<=b. """
    pass

def length_hint(obj, default=0): # real signature unknown; restored from __doc__
    """
    length_hint(obj, default=0) -> int
    Return an estimate of the number of items in obj.
    This is useful for presizing containers when building from an
    iterable.
    
    If the object supports len(), the result will be
    exact. Otherwise, it may over- or under-estimate by an
    arbitrary amount. The result will be an integer >= 0.
    """
    return 0

def lshift(a, b): # real signature unknown; restored from __doc__
    """ lshift(a, b) -- Same as a << b. """
    pass

def lt(a, b): # real signature unknown; restored from __doc__
    """ lt(a, b) -- Same as a<b. """
    pass

def matmul(a, b): # real signature unknown; restored from __doc__
    """ matmul(a, b) -- Same as a @ b. """
    pass

def mod(a, b): # real signature unknown; restored from __doc__
    """ mod(a, b) -- Same as a % b. """
    pass

def mul(a, b): # real signature unknown; restored from __doc__
    """ mul(a, b) -- Same as a * b. """
    pass

def ne(a, b): # real signature unknown; restored from __doc__
    """ ne(a, b) -- Same as a!=b. """
    pass

def neg(a): # real signature unknown; restored from __doc__
    """ neg(a) -- Same as -a. """
    pass

def not_(a): # real signature unknown; restored from __doc__
    """ not_(a) -- Same as not a. """
    pass

def or_(a, b): # real signature unknown; restored from __doc__
    """ or_(a, b) -- Same as a | b. """
    pass

def pos(a): # real signature unknown; restored from __doc__
    """ pos(a) -- Same as +a. """
    pass

def pow(a, b): # real signature unknown; restored from __doc__
    """ pow(a, b) -- Same as a ** b. """
    pass

def rshift(a, b): # real signature unknown; restored from __doc__
    """ rshift(a, b) -- Same as a >> b. """
    pass

def setitem(a, b, c): # real signature unknown; restored from __doc__
    """ setitem(a, b, c) -- Same as a[b] = c. """
    pass

def sub(a, b): # real signature unknown; restored from __doc__
    """ sub(a, b) -- Same as a - b. """
    pass

def truediv(a, b): # real signature unknown; restored from __doc__
    """ truediv(a, b) -- Same as a / b. """
    pass

def truth(a): # real signature unknown; restored from __doc__
    """ truth(a) -- Return True if a is true, False otherwise. """
    pass

def xor(a, b): # real signature unknown; restored from __doc__
    """ xor(a, b) -- Same as a ^ b. """
    pass

def _compare_digest(*args, **kwargs): # real signature unknown
    """
    compare_digest(a, b) -> bool
    
    Return 'a == b'.  This function uses an approach designed to prevent
    timing analysis, making it appropriate for cryptography.
    a and b must both be of the same type: either str (ASCII only),
    or any bytes-like object.
    
    Note: If a and b are of different lengths, or if an error occurs,
    a timing attack could theoretically reveal information about the
    types and lengths of a and b--but not their values.
    """
    pass

# classes

class attrgetter(object):
    """
    attrgetter(attr, ...) --> attrgetter object
    
    Return a callable object that fetches the given attribute(s) from its operand.
    After f = attrgetter('name'), the call f(r) returns r.name.
    After g = attrgetter('name', 'date'), the call g(r) returns (r.name, r.date).
    After h = attrgetter('name.first', 'name.last'), the call h(r) returns
    (r.name.first, r.name.last).
    """
    def __call__(self, *args, **kwargs): # real signature unknown
        """ Call self as a function. """
        pass

    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __init__(self, attr, *more): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __reduce__(self, *args, **kwargs): # real signature unknown
        """ Return state information for pickling """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass


class itemgetter(object):
    """
    itemgetter(item, ...) --> itemgetter object
    
    Return a callable object that fetches the given item(s) from its operand.
    After f = itemgetter(2), the call f(r) returns r[2].
    After g = itemgetter(2, 5, 3), the call g(r) returns (r[2], r[5], r[3])
    """
    def __call__(self, *args, **kwargs): # real signature unknown
        """ Call self as a function. """
        pass

    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __init__(self, item, *more): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __reduce__(self, *args, **kwargs): # real signature unknown
        """ Return state information for pickling """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass


class methodcaller(object):
    """
    methodcaller(name, ...) --> methodcaller object
    
    Return a callable object that calls the given method on its operand.
    After f = methodcaller('name'), the call f(r) returns r.name().
    After g = methodcaller('name', 'date', foo=1), the call g(r) returns
    r.name('date', foo=1).
    """
    def __call__(self, *args, **kwargs): # real signature unknown
        """ Call self as a function. """
        pass

    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __init__(self, name, *more): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __reduce__(self, *args, **kwargs): # real signature unknown
        """ Return state information for pickling """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass


class __loader__(object):
    """
    Meta path import for built-in modules.
    
        All methods are either class or static methods to avoid the need to
        instantiate the class.
    """
    @classmethod
    def create_module(cls, *args, **kwargs): # real signature unknown
        """ Create a built-in module """
        pass

    @classmethod
    def exec_module(cls, *args, **kwargs): # real signature unknown
        """ Exec a built-in module """
        pass

    @classmethod
    def find_module(cls, *args, **kwargs): # real signature unknown
        """
        Find the built-in module.
        
                If 'path' is ever specified then the search is considered a failure.
        
                This method is deprecated.  Use find_spec() instead.
        """
        pass

    @classmethod
    def find_spec(cls, *args, **kwargs): # real signature unknown
        pass

    @classmethod
    def get_code(cls, *args, **kwargs): # real signature unknown
        """ Return None as built-in modules do not have code objects. """
        pass

    @classmethod
    def get_source(cls, *args, **kwargs): # real signature unknown
        """ Return None as built-in modules do not have source code. """
        pass

    @classmethod
    def is_package(cls, *args, **kwargs): # real signature unknown
        """ Return False as built-in modules are never packages. """
        pass

    @classmethod
    def load_module(cls, *args, **kwargs): # real signature unknown
        """
        Load the specified module into sys.modules and return it.
        
            This method is deprecated.  Use loader.exec_module instead.
        """
        pass

    def module_repr(module): # reliably restored by inspect
        """
        Return repr for the module.
        
                The method is deprecated.  The import machinery does the job itself.
        """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""


    __dict__ = None # (!) real value is ''


# variables with complex values

__spec__ = None # (!) real value is ''

