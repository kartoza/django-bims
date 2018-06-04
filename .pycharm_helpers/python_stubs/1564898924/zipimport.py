# encoding: utf-8
# module zipimport
# from (built-in)
# by generator 1.145
"""
zipimport provides support for importing Python modules from Zip archives.

This module exports three objects:
- zipimporter: a class; its constructor takes a path to a Zip archive.
- ZipImportError: exception raised by zipimporter objects. It's a
  subclass of ImportError, so it can be caught as ImportError, too.
- _zip_directory_cache: a dict, mapping archive paths to zip directory
  info dicts, as used in zipimporter._files.

It is usually not needed to use the zipimport module explicitly; it is
used by the builtin import mechanism for sys.path items that are paths
to Zip archives.
"""
# no imports

# no functions
# classes

class zipimporter(object):
    """
    zipimporter(archivepath) -> zipimporter object
    
    Create a new zipimporter instance. 'archivepath' must be a path to
    a zipfile, or to a specific path inside a zipfile. For example, it can be
    '/tmp/myimport.zip', or '/tmp/myimport.zip/mydirectory', if mydirectory is a
    valid directory inside the archive.
    
    'ZipImportError is raised if 'archivepath' doesn't point to a valid Zip
    archive.
    
    The 'archive' attribute of zipimporter objects contains the name of the
    zipfile targeted.
    """
    def find_loader(self, fullname, path=None): # real signature unknown; restored from __doc__
        """
        find_loader(fullname, path=None) -> self, str or None.
        
        Search for a module specified by 'fullname'. 'fullname' must be the
        fully qualified (dotted) module name. It returns the zipimporter
        instance itself if the module was found, a string containing the
        full path name if it's possibly a portion of a namespace package,
        or None otherwise. The optional 'path' argument is ignored -- it's
         there for compatibility with the importer protocol.
        """
        return self

    def find_module(self, fullname, path=None): # real signature unknown; restored from __doc__
        """
        find_module(fullname, path=None) -> self or None.
        
        Search for a module specified by 'fullname'. 'fullname' must be the
        fully qualified (dotted) module name. It returns the zipimporter
        instance itself if the module was found, or None if it wasn't.
        The optional 'path' argument is ignored -- it's there for compatibility
        with the importer protocol.
        """
        return self

    def get_code(self, fullname): # real signature unknown; restored from __doc__
        """
        get_code(fullname) -> code object.
        
        Return the code object for the specified module. Raise ZipImportError
        if the module couldn't be found.
        """
        pass

    def get_data(self, pathname): # real signature unknown; restored from __doc__
        """
        get_data(pathname) -> string with file data.
        
        Return the data associated with 'pathname'. Raise IOError if
        the file wasn't found.
        """
        return ""

    def get_filename(self, fullname): # real signature unknown; restored from __doc__
        """
        get_filename(fullname) -> filename string.
        
        Return the filename for the specified module.
        """
        pass

    def get_source(self, fullname): # real signature unknown; restored from __doc__
        """
        get_source(fullname) -> source string.
        
        Return the source code for the specified module. Raise ZipImportError
        if the module couldn't be found, return None if the archive does
        contain the module, but has no source for it.
        """
        pass

    def is_package(self, fullname): # real signature unknown; restored from __doc__
        """
        is_package(fullname) -> bool.
        
        Return True if the module specified by fullname is a package.
        Raise ZipImportError if the module couldn't be found.
        """
        pass

    def load_module(self, fullname): # real signature unknown; restored from __doc__
        """
        load_module(fullname) -> module.
        
        Load the module specified by 'fullname'. 'fullname' must be the
        fully qualified (dotted) module name. It returns the imported
        module, or raises ZipImportError if it wasn't found.
        """
        pass

    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __init__(self, archivepath): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    archive = property(lambda self: '')
    """:type: string"""

    prefix = property(lambda self: '')
    """:type: string"""

    _files = property(lambda self: {})
    """:type: dict"""



class ZipImportError(ImportError):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



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

_zip_directory_cache = {} # real value of type <class 'dict'> skipped

__spec__ = None # (!) real value is ''

