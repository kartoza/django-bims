# encoding: utf-8
# module greenlet
# from /usr/local/lib/python3.6/site-packages/greenlet.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
# no doc
# no imports

# Variables with simple values

GREENLET_USE_GC = True
GREENLET_USE_TRACING = True

__version__ = '0.4.13'

# functions

def getcurrent(*args, **kwargs): # real signature unknown
    pass

def gettrace(*args, **kwargs): # real signature unknown
    pass

def settrace(*args, **kwargs): # real signature unknown
    pass

# classes

class error(Exception):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



class greenlet(object):
    """
    greenlet(run=None, parent=None) -> greenlet
    
    Creates a new greenlet object (without running it).
    
     - *run* -- The callable to invoke.
     - *parent* -- The parent greenlet. The default is the current greenlet.
    """
    def getcurrent(self, *args, **kwargs): # real signature unknown
        pass

    def gettrace(self, *args, **kwargs): # real signature unknown
        pass

    def settrace(self, *args, **kwargs): # real signature unknown
        pass

    def switch(self, *args, **kwargs): # real signature unknown; restored from __doc__
        """
        switch(*args, **kwargs)
        
        Switch execution to this greenlet.
        
        If this greenlet has never been run, then this greenlet
        will be switched to using the body of self.run(*args, **kwargs).
        
        If the greenlet is active (has been run, but was switch()'ed
        out before leaving its run function), then this greenlet will
        be resumed and the return value to its switch call will be
        None if no arguments are given, the given argument if one
        argument is given, or the args tuple and keyword args dict if
        multiple arguments are given.
        
        If the greenlet is dead, or is the current greenlet then this
        function will simply return the arguments using the same rules as
        above.
        """
        pass

    def throw(self, *args, **kwargs): # real signature unknown
        """
        Switches execution to the greenlet ``g``, but immediately raises the
        given exception in ``g``.  If no argument is provided, the exception
        defaults to ``greenlet.GreenletExit``.  The normal exception
        propagation rules apply, as described above.  Note that calling this
        method is almost equivalent to the following::
        
            def raiser():
                raise typ, val, tb
            g_raiser = greenlet(raiser, parent=g)
            g_raiser.switch()
        
        except that this trick does not work for the
        ``greenlet.GreenletExit`` exception, which would not propagate
        from ``g_raiser`` to ``g``.
        """
        pass

    def __bool__(self, *args, **kwargs): # real signature unknown
        """ self != 0 """
        pass

    def __getstate__(self, *args, **kwargs): # real signature unknown
        pass

    def __init__(self, run=None, parent=None): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    dead = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    gr_frame = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    parent = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    run = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    _stack_saved = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default


    error = error
    GreenletExit = None # (!) forward: GreenletExit, real value is ''
    __dict__ = None # (!) real value is ''


class GreenletExit(BaseException):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



# variables with complex values

_C_API = None # (!) real value is ''

__loader__ = None # (!) real value is ''

__spec__ = None # (!) real value is ''

