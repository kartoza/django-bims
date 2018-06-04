# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


# Variables with simple values

apilevel = '2.0'

paramstyle = 'pyformat'

REPLICATION_LOGICAL = 87654321
REPLICATION_PHYSICAL = 12345678

threadsafety = 2

__libpq_version__ = 100001

__version__ = '2.7.4 (dt dec pq3 ext lo64)'

# functions

def adapt(obj, protocol, alternate): # real signature unknown; restored from __doc__
    """ adapt(obj, protocol, alternate) -> object -- adapt obj to given protocol """
    return object()

def BINARY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def BINARYARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def BOOLEAN(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def BOOLEANARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def CIDRARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def Date(year, month, day): # real signature unknown; restored from __doc__
    """
    Date(year, month, day) -> new date
    
    Build an object holding a date value.
    """
    pass

def DATE(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def DATEARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def DateFromPy(datetime_date): # real signature unknown; restored from __doc__
    """ DateFromPy(datetime.date) -> new wrapper """
    pass

def DateFromTicks(ticks): # real signature unknown; restored from __doc__
    """
    DateFromTicks(ticks) -> new date
    
    Build an object holding a date value from the given ticks value.
    
    Ticks are the number of seconds since the epoch; see the documentation of the standard Python time module for details).
    """
    pass

def DATETIME(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def DATETIMEARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def DATETIMETZ(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def DATETIMETZARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def DECIMAL(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def DECIMALARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def FLOAT(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def FLOATARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def get_wait_callback(*args, **kwargs): # real signature unknown
    """
    Return the currently registered wait callback.
    
    Return `!None` if no callback is currently registered.
    """
    pass

def INETARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def INTEGER(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def INTEGERARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def INTERVAL(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def INTERVALARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def IntervalFromPy(datetime_timedelta): # real signature unknown; restored from __doc__
    """ IntervalFromPy(datetime.timedelta) -> new wrapper """
    pass

def libpq_version(*args, **kwargs): # real signature unknown
    """ Query actual libpq version loaded. """
    pass

def LONGINTEGER(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def LONGINTEGERARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def MACADDRARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def new_array_type(oids, name, baseobj): # real signature unknown; restored from __doc__
    """
    new_array_type(oids, name, baseobj) -> new type object
    
    Create a new binding object to parse an array.
    
    The object can be used with `register_type()`.
    
    :Parameters:
      * `oids`: Tuple of ``oid`` of the PostgreSQL types to convert.
      * `name`: Name for the new type
      * `baseobj`: Adapter to perform type conversion of a single array item.
    """
    pass

def new_type(oids, name, castobj): # real signature unknown; restored from __doc__
    """
    new_type(oids, name, castobj) -> new type object
    
    Create a new binding object. The object can be used with the
    `register_type()` function to bind PostgreSQL objects to python objects.
    
    :Parameters:
      * `oids`: Tuple of ``oid`` of the PostgreSQL types to convert.
      * `name`: Name for the new type
      * `adapter`: Callable to perform type conversion.
        It must have the signature ``fun(value, cur)`` where ``value`` is
        the string representation returned by PostgreSQL (`!None` if ``NULL``)
        and ``cur`` is the cursor from which data are read.
    """
    pass

def NUMBER(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def parse_dsn(dsn): # real signature unknown; restored from __doc__
    """ parse_dsn(dsn) -> dict -- parse a connection string into parameters """
    return {}

def PYDATE(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def PYDATEARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def PYDATETIME(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def PYDATETIMEARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def PYDATETIMETZ(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def PYDATETIMETZARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def PYINTERVAL(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def PYINTERVALARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def PYTIME(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def PYTIMEARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def quote_ident(p_str, conn_or_curs): # real signature unknown; restored from __doc__
    """
    quote_ident(str, conn_or_curs) -> str -- wrapper around PQescapeIdentifier
    
    :Parameters:
      * `str`: A bytes or unicode object
      * `conn_or_curs`: A connection or cursor, required
    """
    return ""

def register_type(obj, conn_or_curs): # real signature unknown; restored from __doc__
    """
    register_type(obj, conn_or_curs) -> None -- register obj with psycopg type system
    
    :Parameters:
      * `obj`: A type adapter created by `new_type()`
      * `conn_or_curs`: A connection, cursor or None
    """
    pass

def ROWID(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def ROWIDARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def set_wait_callback(None_): # real signature unknown; restored from __doc__
    """
    Register a callback function to block waiting for data.
    
    The callback should have signature :samp:`fun({conn})` and
    is called to wait for data available whenever a blocking function from the
    libpq is called.  Use `!set_wait_callback(None)` to revert to the
    original behaviour (i.e. using blocking libpq functions).
    
    The function is an hook to allow coroutine-based libraries (such as
    Eventlet_ or gevent_) to switch when Psycopg is blocked, allowing
    other coroutines to run concurrently.
    
    See `~psycopg2.extras.wait_select()` for an example of a wait callback
    implementation.
    
    .. _Eventlet: http://eventlet.net/
    .. _gevent: http://www.gevent.org/
    """
    pass

def STRING(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def STRINGARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def Time(hour, minutes, seconds, tzinfo=None): # real signature unknown; restored from __doc__
    """
    Time(hour, minutes, seconds, tzinfo=None) -> new time
    
    Build an object holding a time value.
    """
    pass

def TIME(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def TIMEARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def TimeFromPy(datetime_time): # real signature unknown; restored from __doc__
    """ TimeFromPy(datetime.time) -> new wrapper """
    pass

def TimeFromTicks(ticks): # real signature unknown; restored from __doc__
    """
    TimeFromTicks(ticks) -> new time
    
    Build an object holding a time value from the given ticks value.
    
    Ticks are the number of seconds since the epoch; see the documentation of the standard Python time module for details).
    """
    pass

def Timestamp(year, month, day, hour, minutes, seconds, tzinfo=None): # real signature unknown; restored from __doc__
    """
    Timestamp(year, month, day, hour, minutes, seconds, tzinfo=None) -> new timestamp
    
    Build an object holding a timestamp value.
    """
    pass

def TimestampFromPy(datetime_datetime): # real signature unknown; restored from __doc__
    """ TimestampFromPy(datetime.datetime) -> new wrapper """
    pass

def TimestampFromTicks(ticks): # real signature unknown; restored from __doc__
    """
    TimestampFromTicks(ticks) -> new timestamp
    
    Build an object holding a timestamp value from the given ticks value.
    
    Ticks are the number of seconds since the epoch; see the documentation of the standard Python time module for details).
    """
    pass

def UNICODE(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def UNICODEARRAY(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def UNKNOWN(*args, **kwargs): # real signature unknown
    """ psycopg type-casting object """
    pass

def _connect(dsn, connection_factory=None, *args, **kwargs): # real signature unknown; NOTE: unreliably restored from __doc__ 
    """ _connect(dsn, [connection_factory], [async]) -- New database connection. """
    pass

# classes

from .AsIs import AsIs
from .Binary import Binary
from .Boolean import Boolean
from .Column import Column
from .connection import connection
from .cursor import cursor
from .Error import Error
from .DatabaseError import DatabaseError
from .DataError import DataError
from .Decimal import Decimal
from .Diagnostics import Diagnostics
from .Float import Float
from .Int import Int
from .IntegrityError import IntegrityError
from .InterfaceError import InterfaceError
from .InternalError import InternalError
from .ISQLQuote import ISQLQuote
from .List import List
from .lobject import lobject
from .Notify import Notify
from .NotSupportedError import NotSupportedError
from .OperationalError import OperationalError
from .ProgrammingError import ProgrammingError
from .QueryCanceledError import QueryCanceledError
from .QuotedString import QuotedString
from .ReplicationConnection import ReplicationConnection
from .ReplicationCursor import ReplicationCursor
from .ReplicationMessage import ReplicationMessage
from .TransactionRollbackError import TransactionRollbackError
from .Warning import Warning
from .Xid import Xid
# variables with complex values

adapters = {
    (
        float,
        ISQLQuote,
    ): 
        Float
    ,
    (
        int,
        '<value is a self-reference, replaced by this string>',
    ): 
        Int
    ,
    (
        bool,
        '<value is a self-reference, replaced by this string>',
    ): 
        Boolean
    ,
    (
        str,
        '<value is a self-reference, replaced by this string>',
    ): 
        QuotedString
    ,
    (
        bytes,
        '<value is a self-reference, replaced by this string>',
    ): 
        Binary
    ,
    (
        bytearray,
        '<value is a self-reference, replaced by this string>',
    ): 
        '<value is a self-reference, replaced by this string>'
    ,
    (
        memoryview,
        '<value is a self-reference, replaced by this string>',
    ): 
        '<value is a self-reference, replaced by this string>'
    ,
    (
        list,
        '<value is a self-reference, replaced by this string>',
    ): 
        List
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) forward: DateFromPy, real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) forward: TimeFromPy, real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) forward: TimestampFromPy, real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) forward: IntervalFromPy, real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) real value is ''
    ,
    (
        tuple,
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        None # (!) real value is ''
    ,
    (
        None, # (!) real value is ''
        '<value is a self-reference, replaced by this string>',
    ): 
        Decimal
    ,
}

binary_types = {}

encodings = {
    'ABC': 'cp1258',
    'ALT': 'cp866',
    'BIG5': 'big5',
    'EUCCN': 'euccn',
    'EUCJIS2004': 'euc_jis_2004',
    'EUCJP': 'euc_jp',
    'EUCKR': 'euc_kr',
    'EUC_CN': 'euccn',
    'EUC_JIS_2004': 'euc_jis_2004',
    'EUC_JP': 'euc_jp',
    'EUC_KR': 'euc_kr',
    'GB18030': 'gb18030',
    'GBK': 'gbk',
    'ISO88591': 'iso8859_1',
    'ISO885910': 'iso8859_10',
    'ISO885913': 'iso8859_13',
    'ISO885914': 'iso8859_14',
    'ISO885915': 'iso8859_15',
    'ISO885916': 'iso8859_16',
    'ISO88592': 'iso8859_2',
    'ISO88593': 'iso8859_3',
    'ISO88595': 'iso8859_5',
    'ISO88596': 'iso8859_6',
    'ISO88597': 'iso8859_7',
    'ISO88598': 'iso8859_8',
    'ISO88599': 'iso8859_9',
    'ISO_8859_1': 'iso8859_1',
    'ISO_8859_10': 'iso8859_10',
    'ISO_8859_13': 'iso8859_13',
    'ISO_8859_14': 'iso8859_14',
    'ISO_8859_15': 'iso8859_15',
    'ISO_8859_16': 'iso8859_16',
    'ISO_8859_2': 'iso8859_2',
    'ISO_8859_3': 'iso8859_3',
    'ISO_8859_5': 'iso8859_5',
    'ISO_8859_6': 'iso8859_6',
    'ISO_8859_7': 'iso8859_7',
    'ISO_8859_8': 'iso8859_8',
    'ISO_8859_9': 'iso8859_9',
    'JOHAB': 'johab',
    'KOI8': 'koi8_r',
    'KOI8R': 'koi8_r',
    'KOI8U': 'koi8_u',
    'LATIN1': 'iso8859_1',
    'LATIN10': 'iso8859_16',
    'LATIN2': 'iso8859_2',
    'LATIN3': 'iso8859_3',
    'LATIN4': 'iso8859_4',
    'LATIN5': 'iso8859_9',
    'LATIN6': 'iso8859_10',
    'LATIN7': 'iso8859_13',
    'LATIN8': 'iso8859_14',
    'LATIN9': 'iso8859_15',
    'MSKANJI': 'cp932',
    'Mskanji': 'cp932',
    'SHIFTJIS': 'cp932',
    'SHIFTJIS2004': 'shift_jis_2004',
    'SHIFT_JIS_2004': 'shift_jis_2004',
    'SJIS': 'cp932',
    'SQLASCII': 'ascii',
    'SQL_ASCII': 'ascii',
    'ShiftJIS': 'cp932',
    'TCVN': 'cp1258',
    'TCVN5712': 'cp1258',
    'UHC': 'cp949',
    'UNICODE': 'utf_8',
    'UTF8': 'utf_8',
    'VSCII': 'cp1258',
    'WIN': 'cp1251',
    'WIN1250': 'cp1250',
    'WIN1251': 'cp1251',
    'WIN1252': 'cp1252',
    'WIN1253': 'cp1253',
    'WIN1254': 'cp1254',
    'WIN1255': 'cp1255',
    'WIN1256': 'cp1256',
    'WIN1257': 'cp1257',
    'WIN1258': 'cp1258',
    'WIN866': 'cp866',
    'WIN874': 'cp874',
    'WIN932': 'cp932',
    'WIN936': 'gbk',
    'WIN949': 'cp949',
    'WIN950': 'cp950',
    'WINDOWS932': 'cp932',
    'WINDOWS936': 'gbk',
    'WINDOWS949': 'cp949',
    'WINDOWS950': 'cp950',
    'Windows932': 'cp932',
    'Windows936': 'gbk',
    'Windows949': 'cp949',
    'Windows950': 'cp950',
}

string_types = {} # real value of type <class 'dict'> replaced

__loader__ = None # (!) real value is ''

__spec__ = None # (!) real value is ''

