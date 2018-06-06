# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


from .object import object

class Diagnostics(object):
    """
    Details from a database error report.
    
    The object is returned by the `~psycopg2.Error.diag` attribute of the
    `!Error` object.
    All the information available from the |PQresultErrorField|_ function
    are exposed as attributes by the object, e.g. the `!severity` attribute
    returns the `!PG_DIAG_SEVERITY` code. Please refer to the `PostgreSQL documentation`__ for the meaning of all the attributes.
    
    .. |PQresultErrorField| replace:: `!PQresultErrorField()`
    .. _PQresultErrorField: http://www.postgresql.org/docs/current/static/libpq-exec.html#LIBPQ-PQRESULTERRORFIELD
    .. __: PQresultErrorField_
    """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    column_name = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    constraint_name = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    context = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    datatype_name = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    internal_position = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    internal_query = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    message_detail = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    message_hint = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    message_primary = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    schema_name = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    severity = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    source_file = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    source_function = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    source_line = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    sqlstate = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    statement_position = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    table_name = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default



