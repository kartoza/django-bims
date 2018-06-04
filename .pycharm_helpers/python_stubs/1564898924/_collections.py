# encoding: utf-8
# module _collections
# from (built-in)
# by generator 1.145
"""
High performance data structures.
- deque:        ordered collection accessible from endpoints only
- defaultdict:  dict subclass with a default value factory
"""
# no imports

# functions

def _count_elements(mapping, iterable): # real signature unknown; restored from __doc__
    """
    _count_elements(mapping, iterable) -> None
    
    Count elements in the iterable, updating the mapping
    """
    pass

# classes

class defaultdict(dict):
    """
    defaultdict(default_factory[, ...]) --> dict with default factory
    
    The default factory is called without arguments to produce
    a new value when a key is not present, in __getitem__ only.
    A defaultdict compares equal to a dict with the same items.
    All remaining arguments are treated the same as if they were
    passed to the dict constructor, including keyword arguments.
    """
    def copy(self): # real signature unknown; restored from __doc__
        """ D.copy() -> a shallow copy of D. """
        pass

    def __copy__(self, *args, **kwargs): # real signature unknown
        """ D.copy() -> a shallow copy of D. """
        pass

    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __init__(self, default_factory=None, **kwargs): # known case of _collections.defaultdict.__init__
        """
        defaultdict(default_factory[, ...]) --> dict with default factory
        
        The default factory is called without arguments to produce
        a new value when a key is not present, in __getitem__ only.
        A defaultdict compares equal to a dict with the same items.
        All remaining arguments are treated the same as if they were
        passed to the dict constructor, including keyword arguments.
        
        # (copied from class doc)
        """
        pass

    def __missing__(self, key): # real signature unknown; restored from __doc__
        """
        __missing__(key) # Called by __getitem__ for missing key; pseudo-code:
          if self.default_factory is None: raise KeyError((key,))
          self[key] = value = self.default_factory()
          return value
        """
        pass

    def __reduce__(self, *args, **kwargs): # real signature unknown
        """ Return state information for pickling. """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    default_factory = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Factory for default value called by __missing__()."""



class deque(object):
    """
    deque([iterable[, maxlen]]) --> deque object
    
    A list-like sequence optimized for data accesses near its endpoints.
    """
    def append(self, *args, **kwargs): # real signature unknown
        """ Add an element to the right side of the deque. """
        pass

    def appendleft(self, *args, **kwargs): # real signature unknown
        """ Add an element to the left side of the deque. """
        pass

    def clear(self, *args, **kwargs): # real signature unknown
        """ Remove all elements from the deque. """
        pass

    def copy(self, *args, **kwargs): # real signature unknown
        """ Return a shallow copy of a deque. """
        pass

    def count(self, value): # real signature unknown; restored from __doc__
        """ D.count(value) -> integer -- return number of occurrences of value """
        return 0

    def extend(self, *args, **kwargs): # real signature unknown
        """ Extend the right side of the deque with elements from the iterable """
        pass

    def extendleft(self, *args, **kwargs): # real signature unknown
        """ Extend the left side of the deque with elements from the iterable """
        pass

    def index(self, value, start=None, stop=None): # real signature unknown; restored from __doc__
        """
        D.index(value, [start, [stop]]) -> integer -- return first index of value.
        Raises ValueError if the value is not present.
        """
        return 0

    def insert(self, index, p_object): # real signature unknown; restored from __doc__
        """ D.insert(index, object) -- insert object before index """
        pass

    def pop(self, *args, **kwargs): # real signature unknown
        """ Remove and return the rightmost element. """
        pass

    def popleft(self, *args, **kwargs): # real signature unknown
        """ Remove and return the leftmost element. """
        pass

    def remove(self, value): # real signature unknown; restored from __doc__
        """ D.remove(value) -- remove first occurrence of value. """
        pass

    def reverse(self): # real signature unknown; restored from __doc__
        """ D.reverse() -- reverse *IN PLACE* """
        pass

    def rotate(self, *args, **kwargs): # real signature unknown
        """ Rotate the deque n steps to the right (default n=1).  If n is negative, rotates left. """
        pass

    def __add__(self, *args, **kwargs): # real signature unknown
        """ Return self+value. """
        pass

    def __bool__(self, *args, **kwargs): # real signature unknown
        """ self != 0 """
        pass

    def __contains__(self, *args, **kwargs): # real signature unknown
        """ Return key in self. """
        pass

    def __copy__(self, *args, **kwargs): # real signature unknown
        """ Return a shallow copy of a deque. """
        pass

    def __delitem__(self, *args, **kwargs): # real signature unknown
        """ Delete self[key]. """
        pass

    def __eq__(self, *args, **kwargs): # real signature unknown
        """ Return self==value. """
        pass

    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
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

    def __iadd__(self, *args, **kwargs): # real signature unknown
        """ Implement self+=value. """
        pass

    def __imul__(self, *args, **kwargs): # real signature unknown
        """ Implement self*=value. """
        pass

    def __init__(self, iterable=(), maxlen=None): # known case of _collections.deque.__init__
        """
        deque([iterable[, maxlen]]) --> deque object
        
        A list-like sequence optimized for data accesses near its endpoints.
        # (copied from class doc)
        """
        pass

    def __iter__(self, *args, **kwargs): # real signature unknown
        """ Implement iter(self). """
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

    def __mul__(self, *args, **kwargs): # real signature unknown
        """ Return self*value.n """
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __ne__(self, *args, **kwargs): # real signature unknown
        """ Return self!=value. """
        pass

    def __reduce__(self, *args, **kwargs): # real signature unknown
        """ Return state information for pickling. """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    def __reversed__(self): # real signature unknown; restored from __doc__
        """ D.__reversed__() -- return a reverse iterator over the deque """
        pass

    def __rmul__(self, *args, **kwargs): # real signature unknown
        """ Return self*value. """
        pass

    def __setitem__(self, *args, **kwargs): # real signature unknown
        """ Set self[key] to value. """
        pass

    def __sizeof__(self): # real signature unknown; restored from __doc__
        """ D.__sizeof__() -- size of D in memory, in bytes """
        pass

    maxlen = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """maximum size of a deque or None if unbounded"""


    __hash__ = None


class OrderedDict(dict):
    """ Dictionary that remembers insertion order """
    def clear(self): # real signature unknown; restored from __doc__
        """ od.clear() -> None.  Remove all items from od. """
        pass

    def copy(self): # real signature unknown; restored from __doc__
        """ od.copy() -> a shallow copy of od """
        pass

    @classmethod
    def fromkeys(cls, S, v=None): # real signature unknown; restored from __doc__
        """
        OD.fromkeys(S[, v]) -> New ordered dictionary with keys from S.
                If not specified, the value defaults to None.
        """
        pass

    def items(self, *args, **kwargs): # real signature unknown
        pass

    def keys(self, *args, **kwargs): # real signature unknown
        pass

    def move_to_end(self, *args, **kwargs): # real signature unknown
        """
        Move an existing element to the end (or beginning if last==False).
        
                Raises KeyError if the element does not exist.
                When last=True, acts like a fast version of self[key]=self.pop(key).
        """
        pass

    def pop(self, k, d=None): # real signature unknown; restored from __doc__
        """
        od.pop(k[,d]) -> v, remove specified key and return the corresponding
                value.  If key is not found, d is returned if given, otherwise KeyError
                is raised.
        """
        pass

    def popitem(self, *args, **kwargs): # real signature unknown
        """
        Remove and return a (key, value) pair from the dictionary.
        
        Pairs are returned in LIFO order if last is true or FIFO order if false.
        """
        pass

    def setdefault(self, k, d=None): # real signature unknown; restored from __doc__
        """ od.setdefault(k[,d]) -> od.get(k,d), also set od[k]=d if k not in od """
        pass

    def update(self, *args, **kwargs): # real signature unknown
        pass

    def values(self, *args, **kwargs): # real signature unknown
        pass

    def __delitem__(self, *args, **kwargs): # real signature unknown
        """ Delete self[key]. """
        pass

    def __eq__(self, *args, **kwargs): # real signature unknown
        """ Return self==value. """
        pass

    def __ge__(self, *args, **kwargs): # real signature unknown
        """ Return self>=value. """
        pass

    def __gt__(self, *args, **kwargs): # real signature unknown
        """ Return self>value. """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __iter__(self, *args, **kwargs): # real signature unknown
        """ Implement iter(self). """
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

    def __reduce__(self, *args, **kwargs): # real signature unknown
        """ Return state information for pickling """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    def __reversed__(self): # real signature unknown; restored from __doc__
        """ od.__reversed__() <==> reversed(od) """
        pass

    def __setitem__(self, *args, **kwargs): # real signature unknown
        """ Set self[key] to value. """
        pass

    def __sizeof__(self, *args, **kwargs): # real signature unknown
        pass

    __dict__ = None # (!) real value is ''
    __hash__ = None


class _deque_iterator(object):
    # no doc
    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __iter__(self, *args, **kwargs): # real signature unknown
        """ Implement iter(self). """
        pass

    def __length_hint__(self, *args, **kwargs): # real signature unknown
        """ Private method returning an estimate of len(list(it)). """
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __next__(self, *args, **kwargs): # real signature unknown
        """ Implement next(self). """
        pass

    def __reduce__(self, *args, **kwargs): # real signature unknown
        """ Return state information for pickling. """
        pass


class _deque_reverse_iterator(object):
    # no doc
    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __iter__(self, *args, **kwargs): # real signature unknown
        """ Implement iter(self). """
        pass

    def __length_hint__(self, *args, **kwargs): # real signature unknown
        """ Private method returning an estimate of len(list(it)). """
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __next__(self, *args, **kwargs): # real signature unknown
        """ Implement next(self). """
        pass

    def __reduce__(self, *args, **kwargs): # real signature unknown
        """ Return state information for pickling. """
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

