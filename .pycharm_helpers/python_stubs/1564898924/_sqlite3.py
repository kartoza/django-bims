# encoding: utf-8
# module _sqlite3
# from /usr/local/lib/python3.6/lib-dynload/_sqlite3.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
# no doc

# imports
import sqlite3 as __sqlite3


# Variables with simple values

PARSE_COLNAMES = 2
PARSE_DECLTYPES = 1

SQLITE_ALTER_TABLE = 26

SQLITE_ANALYZE = 28
SQLITE_ATTACH = 24

SQLITE_CREATE_INDEX = 1
SQLITE_CREATE_TABLE = 2

SQLITE_CREATE_TEMP_INDEX = 3
SQLITE_CREATE_TEMP_TABLE = 4
SQLITE_CREATE_TEMP_TRIGGER = 5
SQLITE_CREATE_TEMP_VIEW = 6

SQLITE_CREATE_TRIGGER = 7
SQLITE_CREATE_VIEW = 8

SQLITE_DELETE = 9
SQLITE_DENY = 1
SQLITE_DETACH = 25

SQLITE_DROP_INDEX = 10
SQLITE_DROP_TABLE = 11

SQLITE_DROP_TEMP_INDEX = 12
SQLITE_DROP_TEMP_TABLE = 13
SQLITE_DROP_TEMP_TRIGGER = 14
SQLITE_DROP_TEMP_VIEW = 15

SQLITE_DROP_TRIGGER = 16
SQLITE_DROP_VIEW = 17

SQLITE_IGNORE = 2
SQLITE_INSERT = 18
SQLITE_OK = 0
SQLITE_PRAGMA = 19
SQLITE_READ = 20
SQLITE_REINDEX = 27
SQLITE_SELECT = 21
SQLITE_TRANSACTION = 22
SQLITE_UPDATE = 23

sqlite_version = '3.8.7.1'

version = '2.6.0'

# functions

def adapt(obj, protocol, alternate): # real signature unknown; restored from __doc__
    """ adapt(obj, protocol, alternate) -> adapt obj to given protocol. Non-standard. """
    pass

def complete_statement(sql): # real signature unknown; restored from __doc__
    """
    complete_statement(sql)
    
    Checks if a string contains a complete SQL statement. Non-standard.
    """
    pass

def connect(database, timeout=None, detect_types=None, isolation_level=None, check_same_thread=None, factory=None, cached_statements=None, uri=None): # real signature unknown; restored from __doc__
    """
    connect(database[, timeout, detect_types, isolation_level,
            check_same_thread, factory, cached_statements, uri])
    
    Opens a connection to the SQLite database file *database*. You can use
    ":memory:" to open a database connection to a database that resides in
    RAM instead of on disk.
    """
    pass

def enable_callback_tracebacks(flag): # real signature unknown; restored from __doc__
    """
    enable_callback_tracebacks(flag)
    
    Enable or disable callback functions throwing errors to stderr.
    """
    pass

def enable_shared_cache(do_enable): # real signature unknown; restored from __doc__
    """
    enable_shared_cache(do_enable)
    
    Enable or disable shared cache mode for the calling thread.
    Experimental/Non-standard.
    """
    pass

def register_adapter(type, callable): # real signature unknown; restored from __doc__
    """
    register_adapter(type, callable)
    
    Registers an adapter with pysqlite's adapter registry. Non-standard.
    """
    pass

def register_converter(typename, callable): # real signature unknown; restored from __doc__
    """
    register_converter(typename, callable)
    
    Registers a converter with pysqlite. Non-standard.
    """
    pass

# classes

class Cache(object):
    # no doc
    def display(self, *args, **kwargs): # real signature unknown
        """ For debugging only. """
        pass

    def get(self, *args, **kwargs): # real signature unknown
        """ Gets an entry from the cache or calls the factory function to produce one. """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass


class Connection(object):
    """ SQLite database connection object. """
    def close(self, *args, **kwargs): # real signature unknown
        """ Closes the connection. """
        pass

    def commit(self, *args, **kwargs): # real signature unknown
        """ Commit the current transaction. """
        pass

    def create_aggregate(self, *args, **kwargs): # real signature unknown
        """ Creates a new aggregate. Non-standard. """
        pass

    def create_collation(self, *args, **kwargs): # real signature unknown
        """ Creates a collation function. Non-standard. """
        pass

    def create_function(self, *args, **kwargs): # real signature unknown
        """ Creates a new function. Non-standard. """
        pass

    def cursor(self, *args, **kwargs): # real signature unknown
        """ Return a cursor for the connection. """
        pass

    def enable_load_extension(self, *args, **kwargs): # real signature unknown
        """ Enable dynamic loading of SQLite extension modules. Non-standard. """
        pass

    def execute(self, *args, **kwargs): # real signature unknown
        """ Executes a SQL statement. Non-standard. """
        pass

    def executemany(self, *args, **kwargs): # real signature unknown
        """ Repeatedly executes a SQL statement. Non-standard. """
        pass

    def executescript(self, *args, **kwargs): # real signature unknown
        """ Executes a multiple SQL statements at once. Non-standard. """
        pass

    def interrupt(self, *args, **kwargs): # real signature unknown
        """ Abort any pending database operation. Non-standard. """
        pass

    def iterdump(self, *args, **kwargs): # real signature unknown
        """ Returns iterator to the dump of the database in an SQL text format. Non-standard. """
        pass

    def load_extension(self, *args, **kwargs): # real signature unknown
        """ Load SQLite extension module. Non-standard. """
        pass

    def rollback(self, *args, **kwargs): # real signature unknown
        """ Roll back the current transaction. """
        pass

    def set_authorizer(self, *args, **kwargs): # real signature unknown
        """ Sets authorizer callback. Non-standard. """
        pass

    def set_progress_handler(self, *args, **kwargs): # real signature unknown
        """ Sets progress handler callback. Non-standard. """
        pass

    def set_trace_callback(self, *args, **kwargs): # real signature unknown
        """ Sets a trace callback called for each SQL statement (passed as unicode). Non-standard. """
        pass

    def __call__(self, *args, **kwargs): # real signature unknown
        """ Call self as a function. """
        pass

    def __enter__(self, *args, **kwargs): # real signature unknown
        """ For context manager. Non-standard. """
        pass

    def __exit__(self, *args, **kwargs): # real signature unknown
        """ For context manager. Non-standard. """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    DatabaseError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    DataError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    Error = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    IntegrityError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    InterfaceError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    InternalError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    in_transaction = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    isolation_level = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    NotSupportedError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    OperationalError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    ProgrammingError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    row_factory = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    text_factory = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    total_changes = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    Warning = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default



class Cursor(object):
    """ SQLite database cursor class. """
    def close(self, *args, **kwargs): # real signature unknown
        """ Closes the cursor. """
        pass

    def execute(self, *args, **kwargs): # real signature unknown
        """ Executes a SQL statement. """
        pass

    def executemany(self, *args, **kwargs): # real signature unknown
        """ Repeatedly executes a SQL statement. """
        pass

    def executescript(self, *args, **kwargs): # real signature unknown
        """ Executes a multiple SQL statements at once. Non-standard. """
        pass

    def fetchall(self, *args, **kwargs): # real signature unknown
        """ Fetches all rows from the resultset. """
        pass

    def fetchmany(self, *args, **kwargs): # real signature unknown
        """ Fetches several rows from the resultset. """
        pass

    def fetchone(self, *args, **kwargs): # real signature unknown
        """ Fetches one row from the resultset. """
        pass

    def setinputsizes(self, *args, **kwargs): # real signature unknown
        """ Required by DB-API. Does nothing in pysqlite. """
        pass

    def setoutputsize(self, *args, **kwargs): # real signature unknown
        """ Required by DB-API. Does nothing in pysqlite. """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __iter__(self, *args, **kwargs): # real signature unknown
        """ Implement iter(self). """
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __next__(self, *args, **kwargs): # real signature unknown
        """ Implement next(self). """
        pass

    arraysize = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    connection = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    description = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    lastrowid = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    rowcount = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    row_factory = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default



class Error(Exception):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



class DatabaseError(__sqlite3.Error):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass


class DataError(__sqlite3.DatabaseError):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass


class IntegrityError(__sqlite3.DatabaseError):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass


class InterfaceError(__sqlite3.Error):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass


class InternalError(__sqlite3.DatabaseError):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass


class NotSupportedError(__sqlite3.DatabaseError):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass


class OperationalError(__sqlite3.DatabaseError):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass


class OptimizedUnicode(object):
    """
    str(object='') -> str
    str(bytes_or_buffer[, encoding[, errors]]) -> str
    
    Create a new string object from the given object. If encoding or
    errors is specified, then the object must expose a data buffer
    that will be decoded using the given encoding and error handler.
    Otherwise, returns the result of object.__str__() (if defined)
    or repr(object).
    encoding defaults to sys.getdefaultencoding().
    errors defaults to 'strict'.
    """
    def capitalize(self): # real signature unknown; restored from __doc__
        """
        S.capitalize() -> str
        
        Return a capitalized version of S, i.e. make the first character
        have upper case and the rest lower case.
        """
        return ""

    def casefold(self): # real signature unknown; restored from __doc__
        """
        S.casefold() -> str
        
        Return a version of S suitable for caseless comparisons.
        """
        return ""

    def center(self, width, fillchar=None): # real signature unknown; restored from __doc__
        """
        S.center(width[, fillchar]) -> str
        
        Return S centered in a string of length width. Padding is
        done using the specified fill character (default is a space)
        """
        return ""

    def count(self, sub, start=None, end=None): # real signature unknown; restored from __doc__
        """
        S.count(sub[, start[, end]]) -> int
        
        Return the number of non-overlapping occurrences of substring sub in
        string S[start:end].  Optional arguments start and end are
        interpreted as in slice notation.
        """
        return 0

    def encode(self, encoding='utf-8', errors='strict'): # real signature unknown; restored from __doc__
        """
        S.encode(encoding='utf-8', errors='strict') -> bytes
        
        Encode S using the codec registered for encoding. Default encoding
        is 'utf-8'. errors may be given to set a different error
        handling scheme. Default is 'strict' meaning that encoding errors raise
        a UnicodeEncodeError. Other possible values are 'ignore', 'replace' and
        'xmlcharrefreplace' as well as any other name registered with
        codecs.register_error that can handle UnicodeEncodeErrors.
        """
        return b""

    def endswith(self, suffix, start=None, end=None): # real signature unknown; restored from __doc__
        """
        S.endswith(suffix[, start[, end]]) -> bool
        
        Return True if S ends with the specified suffix, False otherwise.
        With optional start, test S beginning at that position.
        With optional end, stop comparing S at that position.
        suffix can also be a tuple of strings to try.
        """
        return False

    def expandtabs(self, tabsize=8): # real signature unknown; restored from __doc__
        """
        S.expandtabs(tabsize=8) -> str
        
        Return a copy of S where all tab characters are expanded using spaces.
        If tabsize is not given, a tab size of 8 characters is assumed.
        """
        return ""

    def find(self, sub, start=None, end=None): # real signature unknown; restored from __doc__
        """
        S.find(sub[, start[, end]]) -> int
        
        Return the lowest index in S where substring sub is found,
        such that sub is contained within S[start:end].  Optional
        arguments start and end are interpreted as in slice notation.
        
        Return -1 on failure.
        """
        return 0

    def format(self, *args, **kwargs): # real signature unknown; restored from __doc__
        """
        S.format(*args, **kwargs) -> str
        
        Return a formatted version of S, using substitutions from args and kwargs.
        The substitutions are identified by braces ('{' and '}').
        """
        return ""

    def format_map(self, mapping): # real signature unknown; restored from __doc__
        """
        S.format_map(mapping) -> str
        
        Return a formatted version of S, using substitutions from mapping.
        The substitutions are identified by braces ('{' and '}').
        """
        return ""

    def index(self, sub, start=None, end=None): # real signature unknown; restored from __doc__
        """
        S.index(sub[, start[, end]]) -> int
        
        Return the lowest index in S where substring sub is found, 
        such that sub is contained within S[start:end].  Optional
        arguments start and end are interpreted as in slice notation.
        
        Raises ValueError when the substring is not found.
        """
        return 0

    def isalnum(self): # real signature unknown; restored from __doc__
        """
        S.isalnum() -> bool
        
        Return True if all characters in S are alphanumeric
        and there is at least one character in S, False otherwise.
        """
        return False

    def isalpha(self): # real signature unknown; restored from __doc__
        """
        S.isalpha() -> bool
        
        Return True if all characters in S are alphabetic
        and there is at least one character in S, False otherwise.
        """
        return False

    def isdecimal(self): # real signature unknown; restored from __doc__
        """
        S.isdecimal() -> bool
        
        Return True if there are only decimal characters in S,
        False otherwise.
        """
        return False

    def isdigit(self): # real signature unknown; restored from __doc__
        """
        S.isdigit() -> bool
        
        Return True if all characters in S are digits
        and there is at least one character in S, False otherwise.
        """
        return False

    def isidentifier(self): # real signature unknown; restored from __doc__
        """
        S.isidentifier() -> bool
        
        Return True if S is a valid identifier according
        to the language definition.
        
        Use keyword.iskeyword() to test for reserved identifiers
        such as "def" and "class".
        """
        return False

    def islower(self): # real signature unknown; restored from __doc__
        """
        S.islower() -> bool
        
        Return True if all cased characters in S are lowercase and there is
        at least one cased character in S, False otherwise.
        """
        return False

    def isnumeric(self): # real signature unknown; restored from __doc__
        """
        S.isnumeric() -> bool
        
        Return True if there are only numeric characters in S,
        False otherwise.
        """
        return False

    def isprintable(self): # real signature unknown; restored from __doc__
        """
        S.isprintable() -> bool
        
        Return True if all characters in S are considered
        printable in repr() or S is empty, False otherwise.
        """
        return False

    def isspace(self): # real signature unknown; restored from __doc__
        """
        S.isspace() -> bool
        
        Return True if all characters in S are whitespace
        and there is at least one character in S, False otherwise.
        """
        return False

    def istitle(self): # real signature unknown; restored from __doc__
        """
        S.istitle() -> bool
        
        Return True if S is a titlecased string and there is at least one
        character in S, i.e. upper- and titlecase characters may only
        follow uncased characters and lowercase characters only cased ones.
        Return False otherwise.
        """
        return False

    def isupper(self): # real signature unknown; restored from __doc__
        """
        S.isupper() -> bool
        
        Return True if all cased characters in S are uppercase and there is
        at least one cased character in S, False otherwise.
        """
        return False

    def join(self, iterable): # real signature unknown; restored from __doc__
        """
        S.join(iterable) -> str
        
        Return a string which is the concatenation of the strings in the
        iterable.  The separator between elements is S.
        """
        return ""

    def ljust(self, width, fillchar=None): # real signature unknown; restored from __doc__
        """
        S.ljust(width[, fillchar]) -> str
        
        Return S left-justified in a Unicode string of length width. Padding is
        done using the specified fill character (default is a space).
        """
        return ""

    def lower(self): # real signature unknown; restored from __doc__
        """
        S.lower() -> str
        
        Return a copy of the string S converted to lowercase.
        """
        return ""

    def lstrip(self, chars=None): # real signature unknown; restored from __doc__
        """
        S.lstrip([chars]) -> str
        
        Return a copy of the string S with leading whitespace removed.
        If chars is given and not None, remove characters in chars instead.
        """
        return ""

    def maketrans(self, *args, **kwargs): # real signature unknown
        """
        Return a translation table usable for str.translate().
        
        If there is only one argument, it must be a dictionary mapping Unicode
        ordinals (integers) or characters to Unicode ordinals, strings or None.
        Character keys will be then converted to ordinals.
        If there are two arguments, they must be strings of equal length, and
        in the resulting dictionary, each character in x will be mapped to the
        character at the same position in y. If there is a third argument, it
        must be a string, whose characters will be mapped to None in the result.
        """
        pass

    def partition(self, sep): # real signature unknown; restored from __doc__
        """
        S.partition(sep) -> (head, sep, tail)
        
        Search for the separator sep in S, and return the part before it,
        the separator itself, and the part after it.  If the separator is not
        found, return S and two empty strings.
        """
        pass

    def replace(self, old, new, count=None): # real signature unknown; restored from __doc__
        """
        S.replace(old, new[, count]) -> str
        
        Return a copy of S with all occurrences of substring
        old replaced by new.  If the optional argument count is
        given, only the first count occurrences are replaced.
        """
        return ""

    def rfind(self, sub, start=None, end=None): # real signature unknown; restored from __doc__
        """
        S.rfind(sub[, start[, end]]) -> int
        
        Return the highest index in S where substring sub is found,
        such that sub is contained within S[start:end].  Optional
        arguments start and end are interpreted as in slice notation.
        
        Return -1 on failure.
        """
        return 0

    def rindex(self, sub, start=None, end=None): # real signature unknown; restored from __doc__
        """
        S.rindex(sub[, start[, end]]) -> int
        
        Return the highest index in S where substring sub is found,
        such that sub is contained within S[start:end].  Optional
        arguments start and end are interpreted as in slice notation.
        
        Raises ValueError when the substring is not found.
        """
        return 0

    def rjust(self, width, fillchar=None): # real signature unknown; restored from __doc__
        """
        S.rjust(width[, fillchar]) -> str
        
        Return S right-justified in a string of length width. Padding is
        done using the specified fill character (default is a space).
        """
        return ""

    def rpartition(self, sep): # real signature unknown; restored from __doc__
        """
        S.rpartition(sep) -> (head, sep, tail)
        
        Search for the separator sep in S, starting at the end of S, and return
        the part before it, the separator itself, and the part after it.  If the
        separator is not found, return two empty strings and S.
        """
        pass

    def rsplit(self, sep=None, maxsplit=-1): # real signature unknown; restored from __doc__
        """
        S.rsplit(sep=None, maxsplit=-1) -> list of strings
        
        Return a list of the words in S, using sep as the
        delimiter string, starting at the end of the string and
        working to the front.  If maxsplit is given, at most maxsplit
        splits are done. If sep is not specified, any whitespace string
        is a separator.
        """
        return []

    def rstrip(self, chars=None): # real signature unknown; restored from __doc__
        """
        S.rstrip([chars]) -> str
        
        Return a copy of the string S with trailing whitespace removed.
        If chars is given and not None, remove characters in chars instead.
        """
        return ""

    def split(self, sep=None, maxsplit=-1): # real signature unknown; restored from __doc__
        """
        S.split(sep=None, maxsplit=-1) -> list of strings
        
        Return a list of the words in S, using sep as the
        delimiter string.  If maxsplit is given, at most maxsplit
        splits are done. If sep is not specified or is None, any
        whitespace string is a separator and empty strings are
        removed from the result.
        """
        return []

    def splitlines(self, keepends=None): # real signature unknown; restored from __doc__
        """
        S.splitlines([keepends]) -> list of strings
        
        Return a list of the lines in S, breaking at line boundaries.
        Line breaks are not included in the resulting list unless keepends
        is given and true.
        """
        return []

    def startswith(self, prefix, start=None, end=None): # real signature unknown; restored from __doc__
        """
        S.startswith(prefix[, start[, end]]) -> bool
        
        Return True if S starts with the specified prefix, False otherwise.
        With optional start, test S beginning at that position.
        With optional end, stop comparing S at that position.
        prefix can also be a tuple of strings to try.
        """
        return False

    def strip(self, chars=None): # real signature unknown; restored from __doc__
        """
        S.strip([chars]) -> str
        
        Return a copy of the string S with leading and trailing
        whitespace removed.
        If chars is given and not None, remove characters in chars instead.
        """
        return ""

    def swapcase(self): # real signature unknown; restored from __doc__
        """
        S.swapcase() -> str
        
        Return a copy of S with uppercase characters converted to lowercase
        and vice versa.
        """
        return ""

    def title(self): # real signature unknown; restored from __doc__
        """
        S.title() -> str
        
        Return a titlecased version of S, i.e. words start with title case
        characters, all remaining cased characters have lower case.
        """
        return ""

    def translate(self, table): # real signature unknown; restored from __doc__
        """
        S.translate(table) -> str
        
        Return a copy of the string S in which each character has been mapped
        through the given translation table. The table must implement
        lookup/indexing via __getitem__, for instance a dictionary or list,
        mapping Unicode ordinals to Unicode ordinals, strings, or None. If
        this operation raises LookupError, the character is left untouched.
        Characters mapped to None are deleted.
        """
        return ""

    def upper(self): # real signature unknown; restored from __doc__
        """
        S.upper() -> str
        
        Return a copy of S converted to uppercase.
        """
        return ""

    def zfill(self, width): # real signature unknown; restored from __doc__
        """
        S.zfill(width) -> str
        
        Pad a numeric string S with zeros on the left, to fill a field
        of the specified width. The string S is never truncated.
        """
        return ""

    def __add__(self, *args, **kwargs): # real signature unknown
        """ Return self+value. """
        pass

    def __contains__(self, *args, **kwargs): # real signature unknown
        """ Return key in self. """
        pass

    def __eq__(self, *args, **kwargs): # real signature unknown
        """ Return self==value. """
        pass

    def __format__(self, format_spec): # real signature unknown; restored from __doc__
        """
        S.__format__(format_spec) -> str
        
        Return a formatted version of S as described by format_spec.
        """
        return ""

    def __getattribute__(self, *args, **kwargs): # real signature unknown
        """ Return getattr(self, name). """
        pass

    def __getitem__(self, *args, **kwargs): # real signature unknown
        """ Return self[key]. """
        pass

    def __getnewargs__(self, *args, **kwargs): # real signature unknown
        pass

    def __ge__(self, *args, **kwargs): # real signature unknown
        """ Return self>=value. """
        pass

    def __gt__(self, *args, **kwargs): # real signature unknown
        """ Return self>value. """
        pass

    def __hash__(self, *args, **kwargs): # real signature unknown
        """ Return hash(self). """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
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

    def __mod__(self, *args, **kwargs): # real signature unknown
        """ Return self%value. """
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

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    def __rmod__(self, *args, **kwargs): # real signature unknown
        """ Return value%self. """
        pass

    def __rmul__(self, *args, **kwargs): # real signature unknown
        """ Return self*value. """
        pass

    def __sizeof__(self): # real signature unknown; restored from __doc__
        """ S.__sizeof__() -> size of S in memory, in bytes """
        pass

    def __str__(self, *args, **kwargs): # real signature unknown
        """ Return str(self). """
        pass


class PrepareProtocol(object):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass


class ProgrammingError(__sqlite3.DatabaseError):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass


class Row(object):
    # no doc
    def keys(self, *args, **kwargs): # real signature unknown
        """ Returns the keys of the row. """
        pass

    def __eq__(self, *args, **kwargs): # real signature unknown
        """ Return self==value. """
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

    def __hash__(self, *args, **kwargs): # real signature unknown
        """ Return hash(self). """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
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

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __ne__(self, *args, **kwargs): # real signature unknown
        """ Return self!=value. """
        pass


class Statement(object):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass


class Warning(Exception):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



# variables with complex values

adapters = {
    (
        None, # (!) real value is ''
        PrepareProtocol,
    ): 
        None # (!) real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) real value is ''
    ,
}

converters = {
    'DATE': None, # (!) real value is ''
    'TIMESTAMP': None, # (!) real value is ''
}

__loader__ = None # (!) real value is ''

__spec__ = None # (!) real value is ''

