# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .object import object

class connection(object):
    """
    connection(dsn, ...) -> new connection object
    
    :Groups:
      * `DBAPI-2.0 errors`: Error, Warning, InterfaceError,
        DatabaseError, InternalError, OperationalError,
        ProgrammingError, IntegrityError, DataError, NotSupportedError
    """
    def cancel(self): # real signature unknown; restored from __doc__
        """ cancel() -- cancel the current operation """
        pass

    def close(self): # real signature unknown; restored from __doc__
        """ close() -- Close the connection. """
        pass

    def commit(self): # real signature unknown; restored from __doc__
        """ commit() -- Commit all changes to database. """
        pass

    def cursor(self, name=None, cursor_factory=None, withhold=False): # real signature unknown; restored from __doc__
        """
        cursor(name=None, cursor_factory=extensions.cursor, withhold=False) -- new cursor
        
        Return a new cursor.
        
        The ``cursor_factory`` argument can be used to
        create non-standard cursors by passing a class different from the
        default. Note that the new class *should* be a sub-class of
        `extensions.cursor`.
        
        :rtype: `extensions.cursor`
        """
        pass

    def fileno(self): # real signature unknown; restored from __doc__
        """ fileno() -> int -- Return file descriptor associated to database connection. """
        return 0

    def get_backend_pid(self): # real signature unknown; restored from __doc__
        """ get_backend_pid() -- Get backend process id. """
        pass

    def get_dsn_parameters(self): # real signature unknown; restored from __doc__
        """ get_dsn_parameters() -- Get effective connection parameters. """
        pass

    def get_parameter_status(self, parameter): # real signature unknown; restored from __doc__
        """
        get_parameter_status(parameter) -- Get backend parameter status.
        
        Potential values for ``parameter``:
          server_version, server_encoding, client_encoding, is_superuser,
          session_authorization, DateStyle, TimeZone, integer_datetimes,
          and standard_conforming_strings
        If server did not report requested parameter, None is returned.
        
        See libpq docs for PQparameterStatus() for further details.
        """
        pass

    def get_transaction_status(self): # real signature unknown; restored from __doc__
        """ get_transaction_status() -- Get backend transaction status. """
        pass

    def isexecuting(self): # real signature unknown; restored from __doc__
        """ isexecuting() -> bool -- Return True if the connection is executing an asynchronous operation. """
        return False

    def lobject(self, oid=0, mode=0, new_oid=0, new_file=None, lobject_factory=None): # real signature unknown; restored from __doc__
        """
        lobject(oid=0, mode=0, new_oid=0, new_file=None,
               lobject_factory=extensions.lobject) -- new lobject
        
        Return a new lobject.
        
        The ``lobject_factory`` argument can be used
        to create non-standard lobjects by passing a class different from the
        default. Note that the new class *should* be a sub-class of
        `extensions.lobject`.
        
        :rtype: `extensions.lobject`
        """
        pass

    def poll(self): # real signature unknown; restored from __doc__
        """ poll() -> int -- Advance the connection or query process without blocking. """
        return 0

    def reset(self): # real signature unknown; restored from __doc__
        """ reset() -- Reset current connection to defaults. """
        pass

    def rollback(self): # real signature unknown; restored from __doc__
        """ rollback() -- Roll back all changes done to database. """
        pass

    def set_client_encoding(self, encoding): # real signature unknown; restored from __doc__
        """ set_client_encoding(encoding) -- Set client encoding to ``encoding``. """
        pass

    def set_isolation_level(self, level): # real signature unknown; restored from __doc__
        """ set_isolation_level(level) -- Switch isolation level to ``level``. """
        pass

    def set_session(self, *more): # real signature unknown; restored from __doc__
        """
        set_session(...) -- Set one or more parameters for the next transactions.
        
        Accepted arguments are 'isolation_level', 'readonly', 'deferrable', 'autocommit'.
        """
        pass

    def tpc_begin(self, xid): # real signature unknown; restored from __doc__
        """ tpc_begin(xid) -- begin a TPC transaction with given transaction ID xid. """
        pass

    def tpc_commit(self, xid=None): # real signature unknown; restored from __doc__
        """ tpc_commit([xid]) -- commit a transaction previously prepared. """
        pass

    def tpc_prepare(self): # real signature unknown; restored from __doc__
        """ tpc_prepare() -- perform the first phase of a two-phase transaction. """
        pass

    def tpc_recover(self): # real signature unknown; restored from __doc__
        """ tpc_recover() -- returns a list of pending transaction IDs. """
        pass

    def tpc_rollback(self, xid=None): # real signature unknown; restored from __doc__
        """ tpc_rollback([xid]) -- abort a transaction previously prepared. """
        pass

    def xid(self, format_id, gtrid, bqual): # real signature unknown; restored from __doc__
        """ xid(format_id, gtrid, bqual) -- create a transaction identifier. """
        pass

    def __enter__(self, *args, **kwargs): # real signature unknown
        """ __enter__ -> self """
        pass

    def __exit__(self, *args, **kwargs): # real signature unknown
        """ __exit__ -- commit if no exception, else roll back """
        pass

    def __init__(self, dsn, *more): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    def __str__(self, *args, **kwargs): # real signature unknown
        """ Return str(self). """
        pass

    async = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """True if the connection is asynchronous."""

    async_ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """True if the connection is asynchronous."""

    autocommit = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Set or return the autocommit status."""

    binary_types = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """A set of typecasters to convert binary values."""

    closed = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """True if the connection is closed."""

    cursor_factory = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Default cursor_factory for cursor()."""

    DatabaseError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Error related to the database engine."""

    DataError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Error related to problems with the processed data."""

    deferrable = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Set or return the connection deferrable status."""

    dsn = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The current connection string."""

    encoding = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The current client encoding."""

    Error = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Base class for error exceptions."""

    IntegrityError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Error related to database integrity."""

    InterfaceError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Error related to the database interface."""

    InternalError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The database encountered an internal error."""

    isolation_level = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Set or return the connection transaction isolation level."""

    notices = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    notifies = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    NotSupportedError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """A method or database API was used which is not supported by the database."""

    OperationalError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Error related to database operation (disconnect, memory allocation etc)."""

    ProgrammingError = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Error related to database programming (SQL error, table not found etc)."""

    protocol_version = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Protocol version used for this connection. Currently always 3."""

    readonly = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Set or return the connection read-only status."""

    server_version = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Server version."""

    status = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The current transaction status."""

    string_types = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """A set of typecasters to convert textual values."""

    Warning = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """A database warning."""



