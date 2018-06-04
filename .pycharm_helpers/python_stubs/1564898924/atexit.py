# encoding: utf-8
# module atexit
# from (built-in)
# by generator 1.145
"""
allow programmer to define multiple exit functions to be executedupon normal program termination.

Two public functions, register and unregister, are defined.
"""
# no imports

# functions

def register(func, *args, **kwargs): # real signature unknown; restored from __doc__
    """
    register(func, *args, **kwargs) -> func
    
    Register a function to be executed upon normal program termination
    
        func - function to be called at exit
        args - optional arguments to pass to func
        kwargs - optional keyword arguments to pass to func
    
        func is returned to facilitate usage as a decorator.
    """
    pass

def unregister(func): # real signature unknown; restored from __doc__
    """
    unregister(func) -> None
    
    Unregister an exit function which was previously registered using
    atexit.register
    
        func - function to be unregistered
    """
    pass

def _clear(): # real signature unknown; restored from __doc__
    """
    _clear() -> None
    
    Clear the list of previously registered exit functions.
    """
    pass

def _ncallbacks(): # real signature unknown; restored from __doc__
    """
    _ncallbacks() -> int
    
    Return the number of registered exit functions.
    """
    return 0

def _run_exitfuncs(): # real signature unknown; restored from __doc__
    """
    _run_exitfuncs() -> None
    
    Run all registered exit functions.
    """
    pass

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

