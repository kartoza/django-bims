# encoding: utf-8
# module unicodedata
# from /usr/local/lib/python3.6/lib-dynload/unicodedata.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
"""
This module provides access to the Unicode Character Database which
defines character properties for all Unicode characters. The data in
this database is based on the UnicodeData.txt file version
9.0.0 which is publically available from ftp://ftp.unicode.org/.

The module uses the same names and symbols as defined by the
UnicodeData File Format 9.0.0.
"""
# no imports

# Variables with simple values

unidata_version = '9.0.0'

# functions

def bidirectional(*args, **kwargs): # real signature unknown
    """
    Returns the bidirectional class assigned to the character chr as string.
    
    If no such value is defined, an empty string is returned.
    """
    pass

def category(*args, **kwargs): # real signature unknown
    """ Returns the general category assigned to the character chr as string. """
    pass

def combining(*args, **kwargs): # real signature unknown
    """
    Returns the canonical combining class assigned to the character chr as integer.
    
    Returns 0 if no combining class is defined.
    """
    pass

def decimal(*args, **kwargs): # real signature unknown
    """
    Converts a Unicode character into its equivalent decimal value.
    
    Returns the decimal value assigned to the character chr as integer.
    If no such value is defined, default is returned, or, if not given,
    ValueError is raised.
    """
    pass

def decomposition(*args, **kwargs): # real signature unknown
    """
    Returns the character decomposition mapping assigned to the character chr as string.
    
    An empty string is returned in case no such mapping is defined.
    """
    pass

def digit(*args, **kwargs): # real signature unknown
    """
    Converts a Unicode character into its equivalent digit value.
    
    Returns the digit value assigned to the character chr as integer.
    If no such value is defined, default is returned, or, if not given,
    ValueError is raised.
    """
    pass

def east_asian_width(*args, **kwargs): # real signature unknown
    """ Returns the east asian width assigned to the character chr as string. """
    pass

def lookup(*args, **kwargs): # real signature unknown
    """
    Look up character by name.
    
    If a character with the given name is found, return the
    corresponding character.  If not found, KeyError is raised.
    """
    pass

def mirrored(*args, **kwargs): # real signature unknown
    """
    Returns the mirrored property assigned to the character chr as integer.
    
    Returns 1 if the character has been identified as a "mirrored"
    character in bidirectional text, 0 otherwise.
    """
    pass

def name(*args, **kwargs): # real signature unknown
    """
    Returns the name assigned to the character chr as a string.
    
    If no name is defined, default is returned, or, if not given,
    ValueError is raised.
    """
    pass

def normalize(*args, **kwargs): # real signature unknown
    """
    Return the normal form 'form' for the Unicode string unistr.
    
    Valid values for form are 'NFC', 'NFKC', 'NFD', and 'NFKD'.
    """
    pass

def numeric(*args, **kwargs): # real signature unknown
    """
    Converts a Unicode character into its equivalent numeric value.
    
    Returns the numeric value assigned to the character chr as float.
    If no such value is defined, default is returned, or, if not given,
    ValueError is raised.
    """
    pass

# classes

class UCD(object):
    # no doc
    def bidirectional(self, *args, **kwargs): # real signature unknown
        """
        Returns the bidirectional class assigned to the character chr as string.
        
        If no such value is defined, an empty string is returned.
        """
        pass

    def category(self, *args, **kwargs): # real signature unknown
        """ Returns the general category assigned to the character chr as string. """
        pass

    def combining(self, *args, **kwargs): # real signature unknown
        """
        Returns the canonical combining class assigned to the character chr as integer.
        
        Returns 0 if no combining class is defined.
        """
        pass

    def decimal(self, *args, **kwargs): # real signature unknown
        """
        Converts a Unicode character into its equivalent decimal value.
        
        Returns the decimal value assigned to the character chr as integer.
        If no such value is defined, default is returned, or, if not given,
        ValueError is raised.
        """
        pass

    def decomposition(self, *args, **kwargs): # real signature unknown
        """
        Returns the character decomposition mapping assigned to the character chr as string.
        
        An empty string is returned in case no such mapping is defined.
        """
        pass

    def digit(self, *args, **kwargs): # real signature unknown
        """
        Converts a Unicode character into its equivalent digit value.
        
        Returns the digit value assigned to the character chr as integer.
        If no such value is defined, default is returned, or, if not given,
        ValueError is raised.
        """
        pass

    def east_asian_width(self, *args, **kwargs): # real signature unknown
        """ Returns the east asian width assigned to the character chr as string. """
        pass

    def lookup(self, *args, **kwargs): # real signature unknown
        """
        Look up character by name.
        
        If a character with the given name is found, return the
        corresponding character.  If not found, KeyError is raised.
        """
        pass

    def mirrored(self, *args, **kwargs): # real signature unknown
        """
        Returns the mirrored property assigned to the character chr as integer.
        
        Returns 1 if the character has been identified as a "mirrored"
        character in bidirectional text, 0 otherwise.
        """
        pass

    def name(self, *args, **kwargs): # real signature unknown
        """
        Returns the name assigned to the character chr as a string.
        
        If no name is defined, default is returned, or, if not given,
        ValueError is raised.
        """
        pass

    def normalize(self, *args, **kwargs): # real signature unknown
        """
        Return the normal form 'form' for the Unicode string unistr.
        
        Valid values for form are 'NFC', 'NFKC', 'NFD', and 'NFKD'.
        """
        pass

    def numeric(self, *args, **kwargs): # real signature unknown
        """
        Converts a Unicode character into its equivalent numeric value.
        
        Returns the numeric value assigned to the character chr as float.
        If no such value is defined, default is returned, or, if not given,
        ValueError is raised.
        """
        pass

    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    unidata_version = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default



# variables with complex values

ucd_3_2_0 = None # (!) real value is ''

ucnhash_CAPI = None # (!) real value is ''

__loader__ = None # (!) real value is ''

__spec__ = None # (!) real value is ''

