# encoding: utf-8
# module _tracemalloc
# from (built-in)
# by generator 1.145
""" Debug module to trace memory blocks allocated by Python. """
# no imports

# functions

def clear_traces(): # real signature unknown; restored from __doc__
    """
    clear_traces()
    
    Clear traces of memory blocks allocated by Python.
    """
    pass

def get_traceback_limit(): # real signature unknown; restored from __doc__
    """
    get_traceback_limit() -> int
    
    Get the maximum number of frames stored in the traceback
    of a trace.
    
    By default, a trace of an allocated memory block only stores
    the most recent frame: the limit is 1.
    """
    return 0

def get_traced_memory(): # real signature unknown; restored from __doc__
    """
    get_traced_memory() -> (int, int)
    
    Get the current size and peak size of memory blocks traced
    by the tracemalloc module as a tuple: (current: int, peak: int).
    """
    pass

def get_tracemalloc_memory(): # real signature unknown; restored from __doc__
    """
    get_tracemalloc_memory() -> int
    
    Get the memory usage in bytes of the tracemalloc module
    used internally to trace memory allocations.
    """
    return 0

def is_tracing(): # real signature unknown; restored from __doc__
    """
    is_tracing()->bool
    
    True if the tracemalloc module is tracing Python memory allocations,
    False otherwise.
    """
    return False

def start(nframe=1): # real signature unknown; restored from __doc__
    """
    start(nframe: int=1)
    
    Start tracing Python memory allocations. Set also the maximum number 
    of frames stored in the traceback of a trace to nframe.
    """
    pass

def stop(): # real signature unknown; restored from __doc__
    """
    stop()
    
    Stop tracing Python memory allocations and clear traces
    of memory blocks allocated by Python.
    """
    pass

def _get_object_traceback(obj): # real signature unknown; restored from __doc__
    """
    _get_object_traceback(obj)
    
    Get the traceback where the Python object obj was allocated.
    Return a tuple of (filename: str, lineno: int) tuples.
    
    Return None if the tracemalloc module is disabled or did not
    trace the allocation of the object.
    """
    pass

def _get_traces(): # real signature unknown; restored from __doc__
    """
    _get_traces() -> list
    
    Get traces of all memory blocks allocated by Python.
    Return a list of (size: int, traceback: tuple) tuples.
    traceback is a tuple of (filename: str, lineno: int) tuples.
    
    Return an empty list if the tracemalloc module is disabled.
    """
    return []

# classes

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

