# encoding: utf-8
# module select
# from /usr/local/lib/python3.6/lib-dynload/select.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
"""
This module supports asynchronous I/O on multiple file descriptors.

*** IMPORTANT NOTICE ***
On Windows, only sockets are supported; on Unix, all file descriptors.
"""
# no imports

# Variables with simple values

EPOLLERR = 8
EPOLLET = 2147483648
EPOLLHUP = 16
EPOLLIN = 1
EPOLLMSG = 1024
EPOLLONESHOT = 1073741824
EPOLLOUT = 4
EPOLLPRI = 2
EPOLLRDBAND = 128
EPOLLRDHUP = 8192
EPOLLRDNORM = 64
EPOLLWRBAND = 512
EPOLLWRNORM = 256

EPOLL_CLOEXEC = 524288

PIPE_BUF = 4096

POLLERR = 8
POLLHUP = 16
POLLIN = 1
POLLMSG = 1024
POLLNVAL = 32
POLLOUT = 4
POLLPRI = 2
POLLRDBAND = 128
POLLRDHUP = 8192
POLLRDNORM = 64
POLLWRBAND = 512
POLLWRNORM = 256

# functions

def poll(*args, **kwargs): # real signature unknown
    """
    Returns a polling object, which supports registering and
    unregistering file descriptors, and then polling them for I/O events.
    """
    pass

def select(rlist, wlist, xlist, timeout=None): # real signature unknown; restored from __doc__
    """
    select(rlist, wlist, xlist[, timeout]) -> (rlist, wlist, xlist)
    
    Wait until one or more file descriptors are ready for some kind of I/O.
    The first three arguments are sequences of file descriptors to be waited for:
    rlist -- wait until ready for reading
    wlist -- wait until ready for writing
    xlist -- wait for an ``exceptional condition''
    If only one kind of condition is required, pass [] for the other lists.
    A file descriptor is either a socket or file object, or a small integer
    gotten from a fileno() method call on one of those.
    
    The optional 4th argument specifies a timeout in seconds; it may be
    a floating point number to specify fractions of seconds.  If it is absent
    or None, the call will never time out.
    
    The return value is a tuple of three lists corresponding to the first three
    arguments; each contains the subset of the corresponding file descriptors
    that are ready.
    
    *** IMPORTANT NOTICE ***
    On Windows, only sockets are supported; on Unix, all file
    descriptors can be used.
    """
    pass

# classes

class epoll(object):
    """
    select.epoll(sizehint=-1, flags=0)
    
    Returns an epolling object
    
    sizehint must be a positive integer or -1 for the default size. The
    sizehint is used to optimize internal data structures. It doesn't limit
    the maximum number of monitored events.
    """
    def close(self): # real signature unknown; restored from __doc__
        """
        close() -> None
        
        Close the epoll control file descriptor. Further operations on the epoll
        object will raise an exception.
        """
        pass

    def fileno(self): # real signature unknown; restored from __doc__
        """
        fileno() -> int
        
        Return the epoll control file descriptor.
        """
        return 0

    @classmethod
    def fromfd(cls, fd): # real signature unknown; restored from __doc__
        """
        fromfd(fd) -> epoll
        
        Create an epoll object from a given control fd.
        """
        return epoll

    def modify(self, fd, eventmask): # real signature unknown; restored from __doc__
        """
        modify(fd, eventmask) -> None
        
        fd is the target file descriptor of the operation
        events is a bit set composed of the various EPOLL constants
        """
        pass

    def poll(self, timeout=-1, maxevents=-1): # real signature unknown; restored from __doc__
        """
        poll([timeout=-1[, maxevents=-1]]) -> [(fd, events), (...)]
        
        Wait for events on the epoll file descriptor for a maximum time of timeout
        in seconds (as float). -1 makes poll wait indefinitely.
        Up to maxevents are returned to the caller.
        """
        pass

    def register(self, fd, eventmask=None): # real signature unknown; restored from __doc__
        """
        register(fd[, eventmask]) -> None
        
        Registers a new fd or raises an OSError if the fd is already registered.
        fd is the target file descriptor of the operation.
        events is a bit set composed of the various EPOLL constants; the default
        is EPOLLIN | EPOLLOUT | EPOLLPRI.
        
        The epoll interface supports all file descriptors that support poll.
        """
        pass

    def unregister(self, fd): # real signature unknown; restored from __doc__
        """
        unregister(fd) -> None
        
        fd is the target file descriptor of the operation.
        """
        pass

    def __enter__(self, *args, **kwargs): # real signature unknown
        pass

    def __exit__(self, *args, **kwargs): # real signature unknown
        pass

    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __init__(self, sizehint=-1, flags=0): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    closed = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """True if the epoll handler is closed"""



class error(Exception):
    """ Base class for I/O related errors. """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __reduce__(self, *args, **kwargs): # real signature unknown
        pass

    def __str__(self, *args, **kwargs): # real signature unknown
        """ Return str(self). """
        pass

    characters_written = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    errno = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """POSIX exception code"""

    filename = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """exception filename"""

    filename2 = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """second exception filename"""

    strerror = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """exception strerror"""



# variables with complex values

__loader__ = None # (!) real value is ''

__spec__ = None # (!) real value is ''

