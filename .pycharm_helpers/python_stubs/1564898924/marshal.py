# encoding: utf-8
# module marshal
# from (built-in)
# by generator 1.145
"""
This module contains functions that can read and write Python values in
a binary format. The format is specific to Python, but independent of
machine architecture issues.

Not all Python object types are supported; in general, only objects
whose value is independent from a particular invocation of Python can be
written and read by this module. The following types are supported:
None, integers, floating point numbers, strings, bytes, bytearrays,
tuples, lists, sets, dictionaries, and code objects, where it
should be understood that tuples, lists and dictionaries are only
supported as long as the values contained therein are themselves
supported; and recursive lists and dictionaries should not be written
(they will cause infinite loops).

Variables:

version -- indicates the format that the module uses. Version 0 is the
    historical format, version 1 shares interned strings and version 2
    uses a binary format for floating point numbers.
    Version 3 shares common object references (New in version 3.4).

Functions:

dump() -- write value to a file
load() -- read value from a file
dumps() -- marshal value as a bytes object
loads() -- read value from a bytes-like object
"""
# no imports

# Variables with simple values

version = 4

# functions

def dump(value, file, version=None): # real signature unknown; restored from __doc__
    """
    dump(value, file[, version])
    
    Write the value on the open file. The value must be a supported type.
    The file must be a writeable binary file.
    
    If the value has (or contains an object that has) an unsupported type, a
    ValueError exception is raised - but garbage data will also be written
    to the file. The object will not be properly read back by load()
    
    The version argument indicates the data format that dump should use.
    """
    pass

def dumps(value, version=None): # real signature unknown; restored from __doc__
    """
    dumps(value[, version])
    
    Return the bytes object that would be written to a file by dump(value, file).
    The value must be a supported type. Raise a ValueError exception if
    value has (or contains an object that has) an unsupported type.
    
    The version argument indicates the data format that dumps should use.
    """
    pass

def load(file): # real signature unknown; restored from __doc__
    """
    load(file)
    
    Read one value from the open file and return it. If no valid value is
    read (e.g. because the data has a different Python version's
    incompatible marshal format), raise EOFError, ValueError or TypeError.
    The file must be a readable binary file.
    
    Note: If an object containing an unsupported type was marshalled with
    dump(), load() will substitute None for the unmarshallable type.
    """
    pass

def loads(bytes): # real signature unknown; restored from __doc__
    """
    loads(bytes)
    
    Convert the bytes-like object to a value. If no valid value is found,
    raise EOFError, ValueError or TypeError. Extra bytes in the input are
    ignored.
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

