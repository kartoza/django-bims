# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .object import object

class cursor(object):
    """ A database cursor. """
    def callproc(self, procname, parameters=None): # real signature unknown; restored from __doc__
        """ callproc(procname, parameters=None) -- Execute stored procedure. """
        pass

    def cast(self, oid, s): # real signature unknown; restored from __doc__
        """
        cast(oid, s) -> value
        
        Convert the string s to a Python object according to its oid.
        
        Look for a typecaster first in the cursor, then in its connection,then in the global register. If no suitable typecaster is found,leave the value as a string.
        """
        pass

    def close(self): # real signature unknown; restored from __doc__
        """ close() -- Close the cursor. """
        pass

    def copy_expert(self, sql, file, size=8192): # real signature unknown; restored from __doc__
        """
        copy_expert(sql, file, size=8192) -- Submit a user-composed COPY statement.
        `file` must be an open, readable file for COPY FROM or an open, writable
        file for COPY TO. The optional `size` argument, when specified for a COPY
        FROM statement, will be passed to file's read method to control the read
        buffer size.
        """
        pass

    def copy_from(self, file, table, sep=None, null=None, size=8192, columns=None): # real signature unknown; restored from __doc__
        """ copy_from(file, table, sep='\t', null='\\N', size=8192, columns=None) -- Copy table from file. """
        pass

    def copy_to(self, file, table, sep=None, null=None, columns=None): # real signature unknown; restored from __doc__
        """ copy_to(file, table, sep='\t', null='\\N', columns=None) -- Copy table to file. """
        pass

    def execute(self, query, vars=None): # real signature unknown; restored from __doc__
        """ execute(query, vars=None) -- Execute query with bound vars. """
        pass

    def executemany(self, query, vars_list): # real signature unknown; restored from __doc__
        """ executemany(query, vars_list) -- Execute many queries with bound vars. """
        pass

    def fetchall(self): # real signature unknown; restored from __doc__
        """
        fetchall() -> list of tuple
        
        Return all the remaining rows of a query result set.
        
        Rows are returned in the form of a list of tuples (by default) or using
        the sequence factory previously set in the `row_factory` attribute.
        Return `!None` when no more data is available.
        """
        return []

    def fetchmany(self, size=None): # real signature unknown; restored from __doc__
        """
        fetchmany(size=self.arraysize) -> list of tuple
        
        Return the next `size` rows of a query result set in the form of a list
        of tuples (by default) or using the sequence factory previously set in
        the `row_factory` attribute.
        
        Return an empty list when no more data is available.
        """
        return []

    def fetchone(self): # real signature unknown; restored from __doc__
        """
        fetchone() -> tuple or None
        
        Return the next row of a query result set in the form of a tuple (by
        default) or using the sequence factory previously set in the
        `row_factory` attribute. Return `!None` when no more data is available.
        """
        return ()

    def mogrify(self, query, vars=None): # real signature unknown; restored from __doc__
        """ mogrify(query, vars=None) -> str -- Return query after vars binding. """
        return ""

    def nextset(self): # real signature unknown; restored from __doc__
        """
        nextset() -- Skip to next set of data.
        
        This method is not supported (PostgreSQL does not have multiple data 
        sets) and will raise a NotSupportedError exception.
        """
        pass

    def scroll(self, value, mode='relative'): # real signature unknown; restored from __doc__
        """ scroll(value, mode='relative') -- Scroll to new position according to mode. """
        pass

    def setinputsizes(self, sizes): # real signature unknown; restored from __doc__
        """
        setinputsizes(sizes) -- Set memory areas before execute.
        
        This method currently does nothing but it is safe to call it.
        """
        pass

    def setoutputsize(self, size, column=None): # real signature unknown; restored from __doc__
        """
        setoutputsize(size, column=None) -- Set column buffer size.
        
        This method currently does nothing but it is safe to call it.
        """
        pass

    def __enter__(self, *args, **kwargs): # real signature unknown
        """ __enter__ -> self """
        pass

    def __exit__(self, *args, **kwargs): # real signature unknown
        """ __exit__ -- close the cursor """
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

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    def __str__(self, *args, **kwargs): # real signature unknown
        """ Return str(self). """
        pass

    arraysize = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Number of records `fetchmany()` must fetch if not explicitly specified."""

    binary_types = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    closed = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """True if cursor is closed, False if cursor is open"""

    connection = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The connection where the cursor comes from."""

    description = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Cursor description as defined in DBAPI-2.0."""

    itersize = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Number of records ``iter(cur)`` must fetch per network roundtrip."""

    lastrowid = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The ``oid`` of the last row inserted by the cursor."""

    name = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    query = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The last query text sent to the backend."""

    rowcount = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Number of rows read from the backend in the last command."""

    rownumber = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The current row position."""

    row_factory = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    scrollable = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Set or return cursor use of SCROLL"""

    statusmessage = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The return message of the last command."""

    string_types = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    typecaster = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    tzinfo_factory = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    withhold = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Set or return cursor use of WITH HOLD"""



