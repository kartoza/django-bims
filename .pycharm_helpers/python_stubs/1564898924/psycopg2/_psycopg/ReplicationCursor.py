# encoding: utf-8
# module psycopg2._psycopg
# from /usr/local/lib/python3.6/site-packages/psycopg2/_psycopg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
""" psycopg PostgreSQL driver """

# imports
import psycopg2 as __psycopg2
import psycopg2.extensions as __psycopg2_extensions


class ReplicationCursor(__psycopg2_extensions.cursor):
    """ A database replication cursor. """
    def consume_stream(self, consumer, keepalive_interval=10): # real signature unknown; restored from __doc__
        """ consume_stream(consumer, keepalive_interval=10) -- Consume replication stream. """
        pass

    def read_message(self): # real signature unknown; restored from __doc__
        """ read_message() -- Try reading a replication message from the server (non-blocking). """
        pass

    def send_feedback(self, write_lsn=0, flush_lsn=0, apply_lsn=0, reply=False): # real signature unknown; restored from __doc__
        """ send_feedback(write_lsn=0, flush_lsn=0, apply_lsn=0, reply=False) -- Try sending a replication feedback message to the server and optionally request a reply. """
        pass

    def start_replication_expert(self, command, decode=False): # real signature unknown; restored from __doc__
        """ start_replication_expert(command, decode=False) -- Start replication with a given command. """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __repr__(self, *args, **kwargs): # real signature unknown
        """ Return repr(self). """
        pass

    def __str__(self, *args, **kwargs): # real signature unknown
        """ Return str(self). """
        pass

    io_timestamp = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """io_timestamp -- the timestamp of latest IO with the server"""



