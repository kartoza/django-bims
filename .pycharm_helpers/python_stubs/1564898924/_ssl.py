# encoding: utf-8
# module _ssl
# from /usr/local/lib/python3.6/lib-dynload/_ssl.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
"""
Implementation module for SSL socket operations.  See the socket module
for documentation.
"""

# imports
import ssl as __ssl


# Variables with simple values

ALERT_DESCRIPTION_ACCESS_DENIED = 49

ALERT_DESCRIPTION_BAD_CERTIFICATE = 42

ALERT_DESCRIPTION_BAD_CERTIFICATE_HASH_VALUE = 114

ALERT_DESCRIPTION_BAD_CERTIFICATE_STATUS_RESPONSE = 113

ALERT_DESCRIPTION_BAD_RECORD_MAC = 20

ALERT_DESCRIPTION_CERTIFICATE_EXPIRED = 45
ALERT_DESCRIPTION_CERTIFICATE_REVOKED = 44
ALERT_DESCRIPTION_CERTIFICATE_UNKNOWN = 46
ALERT_DESCRIPTION_CERTIFICATE_UNOBTAINABLE = 111

ALERT_DESCRIPTION_CLOSE_NOTIFY = 0

ALERT_DESCRIPTION_DECODE_ERROR = 50

ALERT_DESCRIPTION_DECOMPRESSION_FAILURE = 30

ALERT_DESCRIPTION_DECRYPT_ERROR = 51

ALERT_DESCRIPTION_HANDSHAKE_FAILURE = 40

ALERT_DESCRIPTION_ILLEGAL_PARAMETER = 47

ALERT_DESCRIPTION_INSUFFICIENT_SECURITY = 71

ALERT_DESCRIPTION_INTERNAL_ERROR = 80

ALERT_DESCRIPTION_NO_RENEGOTIATION = 100

ALERT_DESCRIPTION_PROTOCOL_VERSION = 70

ALERT_DESCRIPTION_RECORD_OVERFLOW = 22

ALERT_DESCRIPTION_UNEXPECTED_MESSAGE = 10

ALERT_DESCRIPTION_UNKNOWN_CA = 48

ALERT_DESCRIPTION_UNKNOWN_PSK_IDENTITY = 115

ALERT_DESCRIPTION_UNRECOGNIZED_NAME = 112

ALERT_DESCRIPTION_UNSUPPORTED_CERTIFICATE = 43
ALERT_DESCRIPTION_UNSUPPORTED_EXTENSION = 110

ALERT_DESCRIPTION_USER_CANCELLED = 90

CERT_NONE = 0
CERT_OPTIONAL = 1
CERT_REQUIRED = 2

HAS_ALPN = False
HAS_ECDH = True
HAS_NPN = True
HAS_SNI = True

HAS_TLSv1_3 = False

HAS_TLS_UNIQUE = True

OPENSSL_VERSION = 'OpenSSL 1.0.1t  3 May 2016'

OPENSSL_VERSION_NUMBER = 268439887

OP_ALL = 2147484671

OP_CIPHER_SERVER_PREFERENCE = 4194304

OP_NO_COMPRESSION = 131072
OP_NO_SSLv2 = 16777216
OP_NO_SSLv3 = 33554432
OP_NO_TICKET = 16384
OP_NO_TLSv1 = 67108864

OP_NO_TLSv1_1 = 268435456
OP_NO_TLSv1_2 = 134217728
OP_NO_TLSv1_3 = 0

OP_SINGLE_DH_USE = 1048576

OP_SINGLE_ECDH_USE = 524288

PROTOCOL_SSLv23 = 2
PROTOCOL_TLS = 2
PROTOCOL_TLSv1 = 3

PROTOCOL_TLSv1_1 = 4
PROTOCOL_TLSv1_2 = 5

PROTOCOL_TLS_CLIENT = 16
PROTOCOL_TLS_SERVER = 17

SSL_ERROR_EOF = 8

SSL_ERROR_INVALID_ERROR_CODE = 10

SSL_ERROR_SSL = 1
SSL_ERROR_SYSCALL = 5

SSL_ERROR_WANT_CONNECT = 7
SSL_ERROR_WANT_READ = 2
SSL_ERROR_WANT_WRITE = 3

SSL_ERROR_WANT_X509_LOOKUP = 4

SSL_ERROR_ZERO_RETURN = 6

VERIFY_CRL_CHECK_CHAIN = 12
VERIFY_CRL_CHECK_LEAF = 4

VERIFY_DEFAULT = 0

VERIFY_X509_STRICT = 32

# functions

def get_default_verify_paths(*args, **kwargs): # real signature unknown
    """
    Return search paths and environment vars that are used by SSLContext's set_default_verify_paths() to load default CAs.
    
    The values are 'cert_file_env', 'cert_file', 'cert_dir_env', 'cert_dir'.
    """
    pass

def nid2obj(*args, **kwargs): # real signature unknown
    """ Lookup NID, short name, long name and OID of an ASN1_OBJECT by NID. """
    pass

def RAND_add(*args, **kwargs): # real signature unknown
    """
    Mix string into the OpenSSL PRNG state.
    
    entropy (a float) is a lower bound on the entropy contained in
    string.  See RFC 4086.
    """
    pass

def RAND_bytes(*args, **kwargs): # real signature unknown
    """ Generate n cryptographically strong pseudo-random bytes. """
    pass

def RAND_egd(*args, **kwargs): # real signature unknown
    """
    Queries the entropy gather daemon (EGD) on the socket named by 'path'.
    
    Returns number of bytes read.  Raises SSLError if connection to EGD
    fails or if it does not provide enough data to seed PRNG.
    """
    pass

def RAND_pseudo_bytes(*args, **kwargs): # real signature unknown
    """
    Generate n pseudo-random bytes.
    
    Return a pair (bytes, is_cryptographic).  is_cryptographic is True
    if the bytes generated are cryptographically strong.
    """
    pass

def RAND_status(*args, **kwargs): # real signature unknown
    """
    Returns 1 if the OpenSSL PRNG has been seeded with enough data and 0 if not.
    
    It is necessary to seed the PRNG with RAND_add() on some platforms before
    using the ssl() function.
    """
    pass

def txt2obj(*args, **kwargs): # real signature unknown
    """
    Lookup NID, short name, long name and OID of an ASN1_OBJECT.
    
    By default objects are looked up by OID. With name=True short and
    long name are also matched.
    """
    pass

def _test_decode_cert(*args, **kwargs): # real signature unknown
    pass

# classes

class MemoryBIO(object):
    # no doc
    def read(self, *args, **kwargs): # real signature unknown
        """
        Read up to size bytes from the memory BIO.
        
        If size is not specified, read the entire buffer.
        If the return value is an empty bytes instance, this means either
        EOF or that no data is available. Use the "eof" property to
        distinguish between the two.
        """
        pass

    def write(self, *args, **kwargs): # real signature unknown
        """
        Writes the bytes b into the memory BIO.
        
        Returns the number of bytes written.
        """
        pass

    def write_eof(self, *args, **kwargs): # real signature unknown
        """
        Write an EOF marker to the memory BIO.
        
        When all data has been read, the "eof" property will be True.
        """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    eof = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Whether the memory BIO is at EOF."""

    pending = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The number of bytes pending in the memory BIO."""



class SSLError(OSError):
    """ An error occurred in the SSL implementation. """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __str__(self, *args, **kwargs): # real signature unknown
        """ Return str(self). """
        pass


class SSLEOFError(__ssl.SSLError):
    """ SSL/TLS connection terminated abruptly. """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



class SSLSession(object):
    # no doc
    def __eq__(self, *args, **kwargs): # real signature unknown
        """ Return self==value. """
        pass

    def __ge__(self, *args, **kwargs): # real signature unknown
        """ Return self>=value. """
        pass

    def __gt__(self, *args, **kwargs): # real signature unknown
        """ Return self>value. """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __le__(self, *args, **kwargs): # real signature unknown
        """ Return self<=value. """
        pass

    def __lt__(self, *args, **kwargs): # real signature unknown
        """ Return self<value. """
        pass

    def __ne__(self, *args, **kwargs): # real signature unknown
        """ Return self!=value. """
        pass

    has_ticket = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Does the session contain a ticket?"""

    id = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Session id"""

    ticket_lifetime_hint = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Ticket life time hint."""

    time = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Session creation time (seconds since epoch)."""

    timeout = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Session timeout (delta in seconds)."""


    __hash__ = None


class SSLSyscallError(__ssl.SSLError):
    """ System error when attempting SSL operation. """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



class SSLWantReadError(__ssl.SSLError):
    """
    Non-blocking SSL socket needs to read more data
    before the requested operation can be completed.
    """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



class SSLWantWriteError(__ssl.SSLError):
    """
    Non-blocking SSL socket needs to write more data
    before the requested operation can be completed.
    """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



class SSLZeroReturnError(__ssl.SSLError):
    """ SSL/TLS session closed cleanly. """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



class _SSLContext(object):
    # no doc
    def cert_store_stats(self, *args, **kwargs): # real signature unknown
        """
        Returns quantities of loaded X.509 certificates.
        
        X.509 certificates with a CA extension and certificate revocation lists
        inside the context's cert store.
        
        NOTE: Certificates in a capath directory aren't loaded unless they have
        been used at least once.
        """
        pass

    def get_ca_certs(self, *args, **kwargs): # real signature unknown
        """
        Returns a list of dicts with information of loaded CA certs.
        
        If the optional argument is True, returns a DER-encoded copy of the CA
        certificate.
        
        NOTE: Certificates in a capath directory aren't loaded unless they have
        been used at least once.
        """
        pass

    def load_cert_chain(self, *args, **kwargs): # real signature unknown
        pass

    def load_dh_params(self, *args, **kwargs): # real signature unknown
        pass

    def load_verify_locations(self, *args, **kwargs): # real signature unknown
        pass

    def session_stats(self, *args, **kwargs): # real signature unknown
        pass

    def set_ciphers(self, *args, **kwargs): # real signature unknown
        pass

    def set_default_verify_paths(self, *args, **kwargs): # real signature unknown
        pass

    def set_ecdh_curve(self, *args, **kwargs): # real signature unknown
        pass

    def set_servername_callback(self, *args, **kwargs): # real signature unknown
        """
        Set a callback that will be called when a server name is provided by the SSL/TLS client in the SNI extension.
        
        If the argument is None then the callback is disabled. The method is called
        with the SSLSocket, the server name as a string, and the SSLContext object.
        See RFC 6066 for details of the SNI extension.
        """
        pass

    def _set_alpn_protocols(self, *args, **kwargs): # real signature unknown
        pass

    def _set_npn_protocols(self, *args, **kwargs): # real signature unknown
        pass

    def _wrap_bio(self, *args, **kwargs): # real signature unknown
        pass

    def _wrap_socket(self, *args, **kwargs): # real signature unknown
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    check_hostname = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    options = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    verify_flags = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default

    verify_mode = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default



class _SSLSocket(object):
    # no doc
    def cipher(self, *args, **kwargs): # real signature unknown
        pass

    def compression(self, *args, **kwargs): # real signature unknown
        pass

    def do_handshake(self, *args, **kwargs): # real signature unknown
        pass

    def peer_certificate(self, *args, **kwargs): # real signature unknown
        """
        Returns the certificate for the peer.
        
        If no certificate was provided, returns None.  If a certificate was
        provided, but not validated, returns an empty dictionary.  Otherwise
        returns a dict containing information about the peer certificate.
        
        If the optional argument is True, returns a DER-encoded copy of the
        peer certificate, or None if no certificate was provided.  This will
        return the certificate even if it wasn't validated.
        """
        pass

    def pending(self, *args, **kwargs): # real signature unknown
        """ Returns the number of already decrypted bytes available for read, pending on the connection. """
        pass

    def read(self, size, buffer=None): # real signature unknown; restored from __doc__
        """
        read(size, [buffer])
        Read up to size bytes from the SSL socket.
        """
        pass

    def selected_npn_protocol(self, *args, **kwargs): # real signature unknown
        pass

    def shared_ciphers(self, *args, **kwargs): # real signature unknown
        pass

    def shutdown(self, *args, **kwargs): # real signature unknown
        """
        Does the SSL shutdown handshake with the remote end.
        
        Returns the underlying socket object.
        """
        pass

    def tls_unique_cb(self, *args, **kwargs): # real signature unknown
        """
        Returns the 'tls-unique' channel binding data, as defined by RFC 5929.
        
        If the TLS handshake is not yet complete, None is returned.
        """
        pass

    def version(self, *args, **kwargs): # real signature unknown
        pass

    def write(self, *args, **kwargs): # real signature unknown
        """
        Writes the bytes-like object b into the SSL object.
        
        Returns the number of bytes written.
        """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    context = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """_setter_context(ctx)
This changes the context associated with the SSLSocket. This is typically
used from within a callback function set by the set_servername_callback
on the SSLContext to change the certificate information associated with the
SSLSocket before the cryptographic exchange handshake messages
"""

    owner = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The Python-level owner of this object.Passed as "self" in servername callback."""

    server_hostname = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The currently set server hostname (for SNI)."""

    server_side = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Whether this is a server-side socket."""

    session = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """_setter_session(session)
Get / set SSLSession."""

    session_reused = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """Was the client session reused during handshake?"""



# variables with complex values

err_codes_to_names = {
    (
        9,
        100,
    ): 
        'BAD_BASE64_DECODE'
    ,
    (
        9,
        101,
    ): 
        'BAD_DECRYPT'
    ,
    (
        9,
        102,
    ): 
        'BAD_END_LINE'
    ,
    (
        9,
        103,
    ): 
        'BAD_IV_CHARS'
    ,
    (
        9,
        104,
    ): 
        'BAD_PASSWORD_READ'
    ,
    (
        9,
        105,
    ): 
        'NOT_DEK_INFO'
    ,
    (
        9,
        106,
    ): 
        'NOT_ENCRYPTED'
    ,
    (
        9,
        107,
    ): 
        'NOT_PROC_TYPE'
    ,
    (
        9,
        108,
    ): 
        'NO_START_LINE'
    ,
    (
        9,
        109,
    ): 
        'PROBLEMS_GETTING_PASSWORD'
    ,
    (
        9,
        110,
    ): 
        'PUBLIC_KEY_NO_RSA'
    ,
    (
        9,
        111,
    ): 
        'READ_KEY'
    ,
    (
        9,
        112,
    ): 
        'SHORT_HEADER'
    ,
    (
        9,
        113,
    ): 
        'UNSUPPORTED_CIPHER'
    ,
    (
        9,
        114,
    ): 
        'UNSUPPORTED_ENCRYPTION'
    ,
    (
        9,
        115,
    ): 
        'ERROR_CONVERTING_PRIVATE_KEY'
    ,
    (
        9,
        116,
    ): 
        'BAD_MAGIC_NUMBER'
    ,
    (
        9,
        117,
    ): 
        'BAD_VERSION_NUMBER'
    ,
    (
        9,
        118,
    ): 
        'BIO_WRITE_FAILURE'
    ,
    (
        9,
        119,
    ): 
        'EXPECTING_PRIVATE_KEY_BLOB'
    ,
    (
        9,
        120,
    ): 
        'EXPECTING_PUBLIC_KEY_BLOB'
    ,
    (
        9,
        121,
    ): 
        'INCONSISTENT_HEADER'
    ,
    (
        9,
        122,
    ): 
        'KEYBLOB_HEADER_PARSE_ERROR'
    ,
    (
        9,
        123,
    ): 
        'KEYBLOB_TOO_SHORT'
    ,
    (
        9,
        124,
    ): 
        'PVK_DATA_TOO_SHORT'
    ,
    (
        9,
        125,
    ): 
        'PVK_TOO_SHORT'
    ,
    (
        9,
        126,
    ): 
        'UNSUPPORTED_KEY_COMPONENTS'
    ,
    (
        9,
        127,
    ): 
        'CIPHER_IS_NULL'
    ,
    (
        11,
        100,
    ): 
        'BAD_X509_FILETYPE'
    ,
    (
        11,
        101,
    ): 
        'CERT_ALREADY_IN_HASH_TABLE'
    ,
    (
        11,
        102,
    ): 
        'ERR_ASN1_LIB'
    ,
    (
        11,
        103,
    ): 
        'LOADING_CERT_DIR'
    ,
    (
        11,
        104,
    ): 
        'LOADING_DEFAULTS'
    ,
    (
        11,
        105,
    ): 
        'NO_CERT_SET_FOR_US_TO_VERIFY'
    ,
    (
        11,
        106,
    ): 
        'SHOULD_RETRY'
    ,
    (
        11,
        107,
    ): 
        'UNABLE_TO_FIND_PARAMETERS_IN_CHAIN'
    ,
    (
        11,
        108,
    ): 
        'UNABLE_TO_GET_CERTS_PUBLIC_KEY'
    ,
    (
        11,
        109,
    ): 
        'UNKNOWN_NID'
    ,
    (
        11,
        110,
    ): 
        'AKID_MISMATCH'
    ,
    (
        11,
        111,
    ): 
        'UNSUPPORTED_ALGORITHM'
    ,
    (
        11,
        112,
    ): 
        'WRONG_LOOKUP_TYPE'
    ,
    (
        11,
        113,
    ): 
        'INVALID_DIRECTORY'
    ,
    (
        11,
        114,
    ): 
        'CANT_CHECK_DH_KEY'
    ,
    (
        11,
        115,
    ): 
        'KEY_TYPE_MISMATCH'
    ,
    (
        11,
        116,
    ): 
        'KEY_VALUES_MISMATCH'
    ,
    (
        11,
        117,
    ): 
        'UNKNOWN_KEY_TYPE'
    ,
    (
        11,
        118,
    ): 
        'BASE64_DECODE_ERROR'
    ,
    (
        11,
        119,
    ): 
        'INVALID_FIELD_NAME'
    ,
    (
        11,
        120,
    ): 
        'UNKNOWN_TRUST_ID'
    ,
    (
        11,
        121,
    ): 
        'UNKNOWN_PURPOSE_ID'
    ,
    (
        11,
        122,
    ): 
        'WRONG_TYPE'
    ,
    (
        11,
        123,
    ): 
        'INVALID_TRUST'
    ,
    (
        11,
        124,
    ): 
        'METHOD_NOT_SUPPORTED'
    ,
    (
        11,
        125,
    ): 
        'PUBLIC_KEY_DECODE_ERROR'
    ,
    (
        11,
        126,
    ): 
        'PUBLIC_KEY_ENCODE_ERROR'
    ,
    (
        11,
        127,
    ): 
        'CRL_ALREADY_DELTA'
    ,
    (
        11,
        128,
    ): 
        'IDP_MISMATCH'
    ,
    (
        11,
        129,
    ): 
        'ISSUER_MISMATCH'
    ,
    (
        11,
        130,
    ): 
        'NO_CRL_NUMBER'
    ,
    (
        11,
        131,
    ): 
        'CRL_VERIFY_FAILURE'
    ,
    (
        11,
        132,
    ): 
        'NEWER_CRL_NOT_NEWER'
    ,
    (
        20,
        100,
    ): 
        'APP_DATA_IN_HANDSHAKE'
    ,
    (
        20,
        101,
    ): 
        'BAD_ALERT_RECORD'
    ,
    (
        20,
        102,
    ): 
        'BAD_AUTHENTICATION_TYPE'
    ,
    (
        20,
        103,
    ): 
        'BAD_CHANGE_CIPHER_SPEC'
    ,
    (
        20,
        104,
    ): 
        'BAD_CHECKSUM'
    ,
    (
        20,
        105,
    ): 
        'BAD_HELLO_REQUEST'
    ,
    (
        20,
        106,
    ): 
        'BAD_DATA_RETURNED_BY_CALLBACK'
    ,
    (
        20,
        107,
    ): 
        'BAD_DECOMPRESSION'
    ,
    (
        20,
        108,
    ): 
        'BAD_DH_G_LENGTH'
    ,
    (
        20,
        109,
    ): 
        'BAD_DH_PUB_KEY_LENGTH'
    ,
    (
        20,
        110,
    ): 
        'BAD_DH_P_LENGTH'
    ,
    (
        20,
        111,
    ): 
        'BAD_DIGEST_LENGTH'
    ,
    (
        20,
        112,
    ): 
        'BAD_DSA_SIGNATURE'
    ,
    (
        20,
        113,
    ): 
        'BAD_MAC_DECODE'
    ,
    (
        20,
        114,
    ): 
        'BAD_MESSAGE_TYPE'
    ,
    (
        20,
        115,
    ): 
        'BAD_PACKET_LENGTH'
    ,
    (
        20,
        116,
    ): 
        'BAD_PROTOCOL_VERSION_NUMBER'
    ,
    (
        20,
        117,
    ): 
        'BAD_RESPONSE_ARGUMENT'
    ,
    (
        20,
        118,
    ): 
        'BAD_RSA_DECRYPT'
    ,
    (
        20,
        119,
    ): 
        'BAD_RSA_ENCRYPT'
    ,
    (
        20,
        120,
    ): 
        'BAD_RSA_E_LENGTH'
    ,
    (
        20,
        121,
    ): 
        'BAD_RSA_MODULUS_LENGTH'
    ,
    (
        20,
        122,
    ): 
        'BAD_RSA_SIGNATURE'
    ,
    (
        20,
        123,
    ): 
        'BAD_SIGNATURE'
    ,
    (
        20,
        124,
    ): 
        'BAD_SSL_FILETYPE'
    ,
    (
        20,
        125,
    ): 
        'BAD_SSL_SESSION_ID_LENGTH'
    ,
    (
        20,
        126,
    ): 
        'BAD_STATE'
    ,
    (
        20,
        127,
    ): 
        'BAD_WRITE_RETRY'
    ,
    (
        20,
        128,
    ): 
        'BIO_NOT_SET'
    ,
    (
        20,
        129,
    ): 
        'BLOCK_CIPHER_PAD_IS_WRONG'
    ,
    (
        20,
        130,
    ): 
        'BN_LIB'
    ,
    (
        20,
        131,
    ): 
        'CA_DN_LENGTH_MISMATCH'
    ,
    (
        20,
        132,
    ): 
        'CA_DN_TOO_LONG'
    ,
    (
        20,
        133,
    ): 
        'CCS_RECEIVED_EARLY'
    ,
    (
        20,
        134,
    ): 
        'CERTIFICATE_VERIFY_FAILED'
    ,
    (
        20,
        135,
    ): 
        'CERT_LENGTH_MISMATCH'
    ,
    (
        20,
        136,
    ): 
        'CHALLENGE_IS_DIFFERENT'
    ,
    (
        20,
        137,
    ): 
        'CIPHER_CODE_WRONG_LENGTH'
    ,
    (
        20,
        138,
    ): 
        'CIPHER_OR_HASH_UNAVAILABLE'
    ,
    (
        20,
        139,
    ): 
        'CIPHER_TABLE_SRC_ERROR'
    ,
    (
        20,
        140,
    ): 
        'COMPRESSED_LENGTH_TOO_LONG'
    ,
    (
        20,
        141,
    ): 
        'COMPRESSION_FAILURE'
    ,
    (
        20,
        142,
    ): 
        'COMPRESSION_LIBRARY_ERROR'
    ,
    (
        20,
        143,
    ): 
        'CONNECTION_ID_IS_DIFFERENT'
    ,
    (
        20,
        144,
    ): 
        'CONNECTION_TYPE_NOT_SET'
    ,
    (
        20,
        145,
    ): 
        'DATA_BETWEEN_CCS_AND_FINISHED'
    ,
    (
        20,
        146,
    ): 
        'DATA_LENGTH_TOO_LONG'
    ,
    (
        20,
        147,
    ): 
        'DECRYPTION_FAILED'
    ,
    (
        20,
        148,
    ): 
        'DH_PUBLIC_VALUE_LENGTH_IS_WRONG'
    ,
    (
        20,
        149,
    ): 
        'DIGEST_CHECK_FAILED'
    ,
    (
        20,
        150,
    ): 
        'ENCRYPTED_LENGTH_TOO_LONG'
    ,
    (
        20,
        151,
    ): 
        'ERROR_IN_RECEIVED_CIPHER_LIST'
    ,
    (
        20,
        152,
    ): 
        'EXCESSIVE_MESSAGE_SIZE'
    ,
    (
        20,
        153,
    ): 
        'EXTRA_DATA_IN_MESSAGE'
    ,
    (
        20,
        154,
    ): 
        'GOT_A_FIN_BEFORE_A_CCS'
    ,
    (
        20,
        155,
    ): 
        'HTTPS_PROXY_REQUEST'
    ,
    (
        20,
        156,
    ): 
        'HTTP_REQUEST'
    ,
    (
        20,
        157,
    ): 
        'TLS_INVALID_ECPOINTFORMAT_LIST'
    ,
    (
        20,
        158,
    ): 
        'INVALID_CHALLENGE_LENGTH'
    ,
    (
        20,
        159,
    ): 
        'LENGTH_MISMATCH'
    ,
    (
        20,
        160,
    ): 
        'LENGTH_TOO_SHORT'
    ,
    (
        20,
        161,
    ): 
        'LIBRARY_HAS_NO_CIPHERS'
    ,
    (
        20,
        162,
    ): 
        'MISSING_DH_DSA_CERT'
    ,
    (
        20,
        163,
    ): 
        'MISSING_DH_KEY'
    ,
    (
        20,
        164,
    ): 
        'MISSING_DH_RSA_CERT'
    ,
    (
        20,
        165,
    ): 
        'MISSING_DSA_SIGNING_CERT'
    ,
    (
        20,
        166,
    ): 
        'MISSING_EXPORT_TMP_DH_KEY'
    ,
    (
        20,
        167,
    ): 
        'MISSING_EXPORT_TMP_RSA_KEY'
    ,
    (
        20,
        168,
    ): 
        'MISSING_RSA_CERTIFICATE'
    ,
    (
        20,
        169,
    ): 
        'MISSING_RSA_ENCRYPTING_CERT'
    ,
    (
        20,
        170,
    ): 
        'MISSING_RSA_SIGNING_CERT'
    ,
    (
        20,
        171,
    ): 
        'MISSING_TMP_DH_KEY'
    ,
    (
        20,
        172,
    ): 
        'MISSING_TMP_RSA_KEY'
    ,
    (
        20,
        173,
    ): 
        'MISSING_TMP_RSA_PKEY'
    ,
    (
        20,
        174,
    ): 
        'MISSING_VERIFY_MESSAGE'
    ,
    (
        20,
        175,
    ): 
        'NON_SSLV2_INITIAL_PACKET'
    ,
    (
        20,
        176,
    ): 
        'NO_CERTIFICATES_RETURNED'
    ,
    (
        20,
        177,
    ): 
        'NO_CERTIFICATE_ASSIGNED'
    ,
    (
        20,
        178,
    ): 
        'NO_CERTIFICATE_RETURNED'
    ,
    (
        20,
        179,
    ): 
        'NO_CERTIFICATE_SET'
    ,
    (
        20,
        180,
    ): 
        'NO_CERTIFICATE_SPECIFIED'
    ,
    (
        20,
        181,
    ): 
        'NO_CIPHERS_AVAILABLE'
    ,
    (
        20,
        182,
    ): 
        'NO_CIPHERS_PASSED'
    ,
    (
        20,
        183,
    ): 
        'NO_CIPHERS_SPECIFIED'
    ,
    (
        20,
        184,
    ): 
        'NO_CIPHER_LIST'
    ,
    (
        20,
        185,
    ): 
        'NO_CIPHER_MATCH'
    ,
    (
        20,
        186,
    ): 
        'NO_CLIENT_CERT_RECEIVED'
    ,
    (
        20,
        187,
    ): 
        'NO_COMPRESSION_SPECIFIED'
    ,
    (
        20,
        188,
    ): 
        'NO_METHOD_SPECIFIED'
    ,
    (
        20,
        189,
    ): 
        'NO_PRIVATEKEY'
    ,
    (
        20,
        190,
    ): 
        'NO_PRIVATE_KEY_ASSIGNED'
    ,
    (
        20,
        191,
    ): 
        'NO_PROTOCOLS_AVAILABLE'
    ,
    (
        20,
        192,
    ): 
        'NO_PUBLICKEY'
    ,
    (
        20,
        193,
    ): 
        'NO_SHARED_CIPHER'
    ,
    (
        20,
        194,
    ): 
        'NO_VERIFY_CALLBACK'
    ,
    (
        20,
        195,
    ): 
        'NULL_SSL_CTX'
    ,
    (
        20,
        196,
    ): 
        'NULL_SSL_METHOD_PASSED'
    ,
    (
        20,
        197,
    ): 
        'OLD_SESSION_CIPHER_NOT_RETURNED'
    ,
    (
        20,
        198,
    ): 
        'PACKET_LENGTH_TOO_LONG'
    ,
    (
        20,
        199,
    ): 
        'PEER_DID_NOT_RETURN_A_CERTIFICATE'
    ,
    (
        20,
        200,
    ): 
        'PEER_ERROR'
    ,
    (
        20,
        201,
    ): 
        'PEER_ERROR_CERTIFICATE'
    ,
    (
        20,
        202,
    ): 
        'PEER_ERROR_NO_CERTIFICATE'
    ,
    (
        20,
        203,
    ): 
        'PEER_ERROR_NO_CIPHER'
    ,
    (
        20,
        204,
    ): 
        'PEER_ERROR_UNSUPPORTED_CERTIFICATE_TYPE'
    ,
    (
        20,
        205,
    ): 
        'PRE_MAC_LENGTH_TOO_LONG'
    ,
    (
        20,
        206,
    ): 
        'PROBLEMS_MAPPING_CIPHER_FUNCTIONS'
    ,
    (
        20,
        207,
    ): 
        'PROTOCOL_IS_SHUTDOWN'
    ,
    (
        20,
        208,
    ): 
        'PUBLIC_KEY_ENCRYPT_ERROR'
    ,
    (
        20,
        209,
    ): 
        'PUBLIC_KEY_IS_NOT_RSA'
    ,
    (
        20,
        210,
    ): 
        'PUBLIC_KEY_NOT_RSA'
    ,
    (
        20,
        211,
    ): 
        'READ_BIO_NOT_SET'
    ,
    (
        20,
        212,
    ): 
        'READ_WRONG_PACKET_TYPE'
    ,
    (
        20,
        213,
    ): 
        'RECORD_LENGTH_MISMATCH'
    ,
    (
        20,
        214,
    ): 
        'RECORD_TOO_LARGE'
    ,
    (
        20,
        215,
    ): 
        'REQUIRED_CIPHER_MISSING'
    ,
    (
        20,
        216,
    ): 
        'REUSE_CERT_LENGTH_NOT_ZERO'
    ,
    (
        20,
        217,
    ): 
        'REUSE_CERT_TYPE_NOT_ZERO'
    ,
    (
        20,
        218,
    ): 
        'REUSE_CIPHER_LIST_NOT_ZERO'
    ,
    (
        20,
        219,
    ): 
        'SHORT_READ'
    ,
    (
        20,
        220,
    ): 
        'SIGNATURE_FOR_NON_SIGNING_CERTIFICATE'
    ,
    (
        20,
        221,
    ): 
        'SSL23_DOING_SESSION_ID_REUSE'
    ,
    (
        20,
        222,
    ): 
        'SSL3_SESSION_ID_TOO_SHORT'
    ,
    (
        20,
        223,
    ): 
        'PSK_IDENTITY_NOT_FOUND'
    ,
    (
        20,
        224,
    ): 
        'PSK_NO_CLIENT_CB'
    ,
    (
        20,
        225,
    ): 
        'PSK_NO_SERVER_CB'
    ,
    (
        20,
        226,
    ): 
        'CLIENTHELLO_TLSEXT'
    ,
    (
        20,
        227,
    ): 
        'PARSE_TLSEXT'
    ,
    (
        20,
        228,
    ): 
        'SSL_CTX_HAS_NO_DEFAULT_SSL_VERSION'
    ,
    (
        20,
        229,
    ): 
        'SSL_HANDSHAKE_FAILURE'
    ,
    (
        20,
        230,
    ): 
        'SSL_LIBRARY_HAS_NO_CIPHERS'
    ,
    (
        20,
        231,
    ): 
        'SSL_SESSION_ID_IS_DIFFERENT'
    ,
    (
        20,
        232,
    ): 
        'TLS_CLIENT_CERT_REQ_WITH_ANON_CIPHER'
    ,
    (
        20,
        233,
    ): 
        'TLS_PEER_DID_NOT_RESPOND_WITH_CERTIFICATE_LIST'
    ,
    (
        20,
        234,
    ): 
        'TLS_RSA_ENCRYPTED_VALUE_LENGTH_IS_WRONG'
    ,
    (
        20,
        235,
    ): 
        'TRIED_TO_USE_UNSUPPORTED_CIPHER'
    ,
    (
        20,
        236,
    ): 
        'UNABLE_TO_DECODE_DH_CERTS'
    ,
    (
        20,
        237,
    ): 
        'UNABLE_TO_EXTRACT_PUBLIC_KEY'
    ,
    (
        20,
        238,
    ): 
        'UNABLE_TO_FIND_DH_PARAMETERS'
    ,
    (
        20,
        239,
    ): 
        'UNABLE_TO_FIND_PUBLIC_KEY_PARAMETERS'
    ,
    (
        20,
        240,
    ): 
        'UNABLE_TO_FIND_SSL_METHOD'
    ,
    (
        20,
        241,
    ): 
        'UNABLE_TO_LOAD_SSL2_MD5_ROUTINES'
    ,
    (
        20,
        242,
    ): 
        'UNABLE_TO_LOAD_SSL3_MD5_ROUTINES'
    ,
    (
        20,
        243,
    ): 
        'UNABLE_TO_LOAD_SSL3_SHA1_ROUTINES'
    ,
    (
        20,
        244,
    ): 
        'UNEXPECTED_MESSAGE'
    ,
    (
        20,
        245,
    ): 
        'UNEXPECTED_RECORD'
    ,
    (
        20,
        246,
    ): 
        'UNKNOWN_ALERT_TYPE'
    ,
    (
        20,
        247,
    ): 
        'UNKNOWN_CERTIFICATE_TYPE'
    ,
    (
        20,
        248,
    ): 
        'UNKNOWN_CIPHER_RETURNED'
    ,
    (
        20,
        249,
    ): 
        'UNKNOWN_CIPHER_TYPE'
    ,
    (
        20,
        250,
    ): 
        'UNKNOWN_KEY_EXCHANGE_TYPE'
    ,
    (
        20,
        251,
    ): 
        'UNKNOWN_PKEY_TYPE'
    ,
    (
        20,
        252,
    ): 
        'UNKNOWN_PROTOCOL'
    ,
    (
        20,
        253,
    ): 
        'UNKNOWN_REMOTE_ERROR_TYPE'
    ,
    (
        20,
        254,
    ): 
        'UNKNOWN_SSL_VERSION'
    ,
    (
        20,
        255,
    ): 
        'UNKNOWN_STATE'
    ,
    (
        20,
        256,
    ): 
        'UNSUPPORTED_CIPHER'
    ,
    (
        20,
        257,
    ): 
        'UNSUPPORTED_COMPRESSION_ALGORITHM'
    ,
    (
        20,
        258,
    ): 
        'UNSUPPORTED_PROTOCOL'
    ,
    (
        20,
        259,
    ): 
        'UNSUPPORTED_SSL_VERSION'
    ,
    (
        20,
        260,
    ): 
        'WRITE_BIO_NOT_SET'
    ,
    (
        20,
        261,
    ): 
        'WRONG_CIPHER_RETURNED'
    ,
    (
        20,
        262,
    ): 
        'WRONG_MESSAGE_TYPE'
    ,
    (
        20,
        263,
    ): 
        'WRONG_NUMBER_OF_KEY_BITS'
    ,
    (
        20,
        264,
    ): 
        'WRONG_SIGNATURE_LENGTH'
    ,
    (
        20,
        265,
    ): 
        'WRONG_SIGNATURE_SIZE'
    ,
    (
        20,
        266,
    ): 
        'WRONG_SSL_VERSION'
    ,
    (
        20,
        267,
    ): 
        'WRONG_VERSION_NUMBER'
    ,
    (
        20,
        268,
    ): 
        'X509_LIB'
    ,
    (
        20,
        269,
    ): 
        'X509_VERIFICATION_SETUP_PROBLEMS'
    ,
    (
        20,
        270,
    ): 
        'PATH_TOO_LONG'
    ,
    (
        20,
        271,
    ): 
        'BAD_LENGTH'
    ,
    (
        20,
        272,
    ): 
        'ATTEMPT_TO_REUSE_SESSION_IN_DIFFERENT_CONTEXT'
    ,
    (
        20,
        273,
    ): 
        'SSL_SESSION_ID_CONTEXT_TOO_LONG'
    ,
    (
        20,
        274,
    ): 
        'LIBRARY_BUG'
    ,
    (
        20,
        275,
    ): 
        'SERVERHELLO_TLSEXT'
    ,
    (
        20,
        276,
    ): 
        'UNINITIALIZED'
    ,
    (
        20,
        277,
    ): 
        'SESSION_ID_CONTEXT_UNINITIALIZED'
    ,
    (
        20,
        278,
    ): 
        'INVALID_PURPOSE'
    ,
    (
        20,
        279,
    ): 
        'INVALID_TRUST'
    ,
    (
        20,
        280,
    ): 
        'INVALID_COMMAND'
    ,
    (
        20,
        281,
    ): 
        'DECRYPTION_FAILED_OR_BAD_RECORD_MAC'
    ,
    (
        20,
        282,
    ): 
        'ERROR_GENERATING_TMP_RSA_KEY'
    ,
    (
        20,
        283,
    ): 
        'ILLEGAL_PADDING'
    ,
    (
        20,
        284,
    ): 
        'KEY_ARG_TOO_LONG'
    ,
    (
        20,
        285,
    ): 
        'KRB5'
    ,
    (
        20,
        286,
    ): 
        'KRB5_C_CC_PRINC'
    ,
    (
        20,
        287,
    ): 
        'KRB5_C_GET_CRED'
    ,
    (
        20,
        288,
    ): 
        'KRB5_C_INIT'
    ,
    (
        20,
        289,
    ): 
        'KRB5_C_MK_REQ'
    ,
    (
        20,
        290,
    ): 
        'KRB5_S_BAD_TICKET'
    ,
    (
        20,
        291,
    ): 
        'KRB5_S_INIT'
    ,
    (
        20,
        292,
    ): 
        'KRB5_S_RD_REQ'
    ,
    (
        20,
        293,
    ): 
        'KRB5_S_TKT_EXPIRED'
    ,
    (
        20,
        294,
    ): 
        'KRB5_S_TKT_NYV'
    ,
    (
        20,
        295,
    ): 
        'KRB5_S_TKT_SKEW'
    ,
    (
        20,
        296,
    ): 
        'MESSAGE_TOO_LONG'
    ,
    (
        20,
        297,
    ): 
        'ONLY_TLS_ALLOWED_IN_FIPS_MODE'
    ,
    (
        20,
        298,
    ): 
        'RECORD_TOO_SMALL'
    ,
    (
        20,
        299,
    ): 
        'SSL2_CONNECTION_ID_TOO_LONG'
    ,
    (
        20,
        300,
    ): 
        'SSL3_SESSION_ID_TOO_LONG'
    ,
    (
        20,
        301,
    ): 
        'SSL_SESSION_ID_CALLBACK_FAILED'
    ,
    (
        20,
        302,
    ): 
        'SSL_SESSION_ID_CONFLICT'
    ,
    (
        20,
        303,
    ): 
        'SSL_SESSION_ID_HAS_BAD_LENGTH'
    ,
    (
        20,
        304,
    ): 
        'BAD_ECC_CERT'
    ,
    (
        20,
        305,
    ): 
        'BAD_ECDSA_SIGNATURE'
    ,
    (
        20,
        306,
    ): 
        'BAD_ECPOINT'
    ,
    (
        20,
        307,
    ): 
        'COMPRESSION_ID_NOT_WITHIN_PRIVATE_RANGE'
    ,
    (
        20,
        308,
    ): 
        'COOKIE_MISMATCH'
    ,
    (
        20,
        309,
    ): 
        'DUPLICATE_COMPRESSION_ID'
    ,
    (
        20,
        310,
    ): 
        'ECGROUP_TOO_LARGE_FOR_CIPHER'
    ,
    (
        20,
        311,
    ): 
        'MISSING_TMP_ECDH_KEY'
    ,
    (
        20,
        312,
    ): 
        'READ_TIMEOUT_EXPIRED'
    ,
    (
        20,
        313,
    ): 
        'UNABLE_TO_DECODE_ECDH_CERTS'
    ,
    (
        20,
        314,
    ): 
        'UNABLE_TO_FIND_ECDH_PARAMETERS'
    ,
    (
        20,
        315,
    ): 
        'UNSUPPORTED_ELLIPTIC_CURVE'
    ,
    (
        20,
        316,
    ): 
        'BAD_PSK_IDENTITY_HINT_LENGTH'
    ,
    (
        20,
        317,
    ): 
        'ECC_CERT_NOT_FOR_KEY_AGREEMENT'
    ,
    (
        20,
        318,
    ): 
        'ECC_CERT_NOT_FOR_SIGNING'
    ,
    (
        20,
        319,
    ): 
        'SSL3_EXT_INVALID_SERVERNAME'
    ,
    (
        20,
        320,
    ): 
        'SSL3_EXT_INVALID_SERVERNAME_TYPE'
    ,
    (
        20,
        321,
    ): 
        'SSL3_EXT_INVALID_ECPOINTFORMAT'
    ,
    (
        20,
        322,
    ): 
        'ECC_CERT_SHOULD_HAVE_RSA_SIGNATURE'
    ,
    (
        20,
        323,
    ): 
        'ECC_CERT_SHOULD_HAVE_SHA1_SIGNATURE'
    ,
    (
        20,
        324,
    ): 
        'NO_REQUIRED_DIGEST'
    ,
    (
        20,
        325,
    ): 
        'INVALID_TICKET_KEYS_LENGTH'
    ,
    (
        20,
        326,
    ): 
        'UNSUPPORTED_DIGEST_TYPE'
    ,
    (
        20,
        327,
    ): 
        'OPAQUE_PRF_INPUT_TOO_LONG'
    ,
    (
        20,
        328,
    ): 
        'INVALID_STATUS_RESPONSE'
    ,
    (
        20,
        329,
    ): 
        'UNSUPPORTED_STATUS_TYPE'
    ,
    (
        20,
        330,
    ): 
        'NO_GOST_CERTIFICATE_SENT_BY_PEER'
    ,
    (
        20,
        331,
    ): 
        'NO_CLIENT_CERT_METHOD'
    ,
    (
        20,
        332,
    ): 
        'BAD_HANDSHAKE_LENGTH'
    ,
    (
        20,
        333,
    ): 
        'BAD_MAC_LENGTH'
    ,
    (
        20,
        334,
    ): 
        'DTLS_MESSAGE_TOO_BIG'
    ,
    (
        20,
        335,
    ): 
        'RENEGOTIATE_EXT_TOO_LONG'
    ,
    (
        20,
        336,
    ): 
        'RENEGOTIATION_ENCODING_ERR'
    ,
    (
        20,
        337,
    ): 
        'RENEGOTIATION_MISMATCH'
    ,
    (
        20,
        338,
    ): 
        'UNSAFE_LEGACY_RENEGOTIATION_DISABLED'
    ,
    (
        20,
        339,
    ): 
        'NO_RENEGOTIATION'
    ,
    (
        20,
        340,
    ): 
        'INCONSISTENT_COMPRESSION'
    ,
    (
        20,
        341,
    ): 
        'INVALID_COMPRESSION_ALGORITHM'
    ,
    (
        20,
        342,
    ): 
        'REQUIRED_COMPRESSSION_ALGORITHM_MISSING'
    ,
    (
        20,
        343,
    ): 
        'COMPRESSION_DISABLED'
    ,
    (
        20,
        344,
    ): 
        'OLD_SESSION_COMPRESSION_ALGORITHM_NOT_RETURNED'
    ,
    (
        20,
        345,
    ): 
        'SCSV_RECEIVED_WHEN_RENEGOTIATING'
    ,
    (
        20,
        346,
    ): 
        'MULTIPLE_SGC_RESTARTS'
    ,
    (
        20,
        347,
    ): 
        'BAD_SRP_A_LENGTH'
    ,
    (
        20,
        348,
    ): 
        'BAD_SRP_B_LENGTH'
    ,
    (
        20,
        349,
    ): 
        'BAD_SRP_G_LENGTH'
    ,
    (
        20,
        350,
    ): 
        'BAD_SRP_N_LENGTH'
    ,
    (
        20,
        351,
    ): 
        'BAD_SRP_S_LENGTH'
    ,
    (
        20,
        352,
    ): 
        'BAD_SRTP_MKI_VALUE'
    ,
    (
        20,
        353,
    ): 
        'BAD_SRTP_PROTECTION_PROFILE_LIST'
    ,
    (
        20,
        354,
    ): 
        'EMPTY_SRTP_PROTECTION_PROFILE_LIST'
    ,
    (
        20,
        355,
    ): 
        'GOT_NEXT_PROTO_BEFORE_A_CCS'
    ,
    (
        20,
        356,
    ): 
        'GOT_NEXT_PROTO_WITHOUT_EXTENSION'
    ,
    (
        20,
        357,
    ): 
        'INVALID_SRP_USERNAME'
    ,
    (
        20,
        358,
    ): 
        'MISSING_SRP_PARAM'
    ,
    (
        20,
        359,
    ): 
        'NO_SRTP_PROFILES'
    ,
    (
        20,
        360,
    ): 
        'SIGNATURE_ALGORITHMS_ERROR'
    ,
    (
        20,
        361,
    ): 
        'SRP_A_CALC'
    ,
    (
        20,
        362,
    ): 
        'SRTP_COULD_NOT_ALLOCATE_PROFILES'
    ,
    (
        20,
        363,
    ): 
        'SRTP_PROTECTION_PROFILE_LIST_TOO_LONG'
    ,
    (
        20,
        364,
    ): 
        'SRTP_UNKNOWN_PROTECTION_PROFILE'
    ,
    (
        20,
        365,
    ): 
        'TLS_HEARTBEAT_PEER_DOESNT_ACCEPT'
    ,
    (
        20,
        366,
    ): 
        'TLS_HEARTBEAT_PENDING'
    ,
    (
        20,
        367,
    ): 
        'TLS_ILLEGAL_EXPORTER_LABEL'
    ,
    (
        20,
        368,
    ): 
        'UNKNOWN_DIGEST'
    ,
    (
        20,
        369,
    ): 
        'USE_SRTP_NOT_NEGOTIATED'
    ,
    (
        20,
        370,
    ): 
        'WRONG_SIGNATURE_TYPE'
    ,
    (
        20,
        371,
    ): 
        'BAD_SRP_PARAMETERS'
    ,
    (
        20,
        372,
    ): 
        'SSL_NEGATIVE_LENGTH'
    ,
    (
        20,
        373,
    ): 
        'INAPPROPRIATE_FALLBACK'
    ,
    (
        20,
        374,
    ): 
        'ECDH_REQUIRED_FOR_SUITEB_MODE'
    ,
    (
        20,
        376,
    ): 
        'NO_SHARED_SIGATURE_ALGORITHMS'
    ,
    (
        20,
        377,
    ): 
        'CERT_CB_ERROR'
    ,
    (
        20,
        378,
    ): 
        'WRONG_CURVE'
    ,
    (
        20,
        379,
    ): 
        'ONLY_TLS_1_2_ALLOWED_IN_SUITEB_MODE'
    ,
    (
        20,
        380,
    ): 
        'ILLEGAL_SUITEB_DIGEST'
    ,
    (
        20,
        381,
    ): 
        'MISSING_ECDSA_SIGNING_CERT'
    ,
    (
        20,
        382,
    ): 
        'MISSING_ECDH_CERT'
    ,
    (
        20,
        383,
    ): 
        'WRONG_CERTIFICATE_TYPE'
    ,
    (
        20,
        384,
    ): 
        'BAD_VALUE'
    ,
    (
        20,
        385,
    ): 
        'INVALID_NULL_CMD_NAME'
    ,
    (
        20,
        386,
    ): 
        'UNKNOWN_CMD_NAME'
    ,
    (
        20,
        387,
    ): 
        'ONLY_DTLS_1_2_ALLOWED_IN_SUITEB_MODE'
    ,
    (
        20,
        388,
    ): 
        'INVALID_SERVERINFO_DATA'
    ,
    (
        20,
        389,
    ): 
        'NO_PEM_EXTENSIONS'
    ,
    (
        20,
        390,
    ): 
        'BAD_DATA'
    ,
    (
        20,
        391,
    ): 
        'PEM_NAME_BAD_PREFIX'
    ,
    (
        20,
        392,
    ): 
        'PEM_NAME_TOO_SHORT'
    ,
    (
        20,
        396,
    ): 
        'VERSION_TOO_LOW'
    ,
    (
        20,
        397,
    ): 
        'CA_KEY_TOO_SMALL'
    ,
    (
        20,
        398,
    ): 
        'CA_MD_TOO_WEAK'
    ,
    (
        20,
        399,
    ): 
        'EE_KEY_TOO_SMALL'
    ,
    (
        20,
        1010,
    ): 
        'SSLV3_ALERT_UNEXPECTED_MESSAGE'
    ,
    (
        20,
        1020,
    ): 
        'SSLV3_ALERT_BAD_RECORD_MAC'
    ,
    (
        20,
        1021,
    ): 
        'TLSV1_ALERT_DECRYPTION_FAILED'
    ,
    (
        20,
        1022,
    ): 
        'TLSV1_ALERT_RECORD_OVERFLOW'
    ,
    (
        20,
        1030,
    ): 
        'SSLV3_ALERT_DECOMPRESSION_FAILURE'
    ,
    (
        20,
        1040,
    ): 
        'SSLV3_ALERT_HANDSHAKE_FAILURE'
    ,
    (
        20,
        1041,
    ): 
        'SSLV3_ALERT_NO_CERTIFICATE'
    ,
    (
        20,
        1042,
    ): 
        'SSLV3_ALERT_BAD_CERTIFICATE'
    ,
    (
        20,
        1043,
    ): 
        'SSLV3_ALERT_UNSUPPORTED_CERTIFICATE'
    ,
    (
        20,
        1044,
    ): 
        'SSLV3_ALERT_CERTIFICATE_REVOKED'
    ,
    (
        20,
        1045,
    ): 
        'SSLV3_ALERT_CERTIFICATE_EXPIRED'
    ,
    (
        20,
        1046,
    ): 
        'SSLV3_ALERT_CERTIFICATE_UNKNOWN'
    ,
    (
        20,
        1047,
    ): 
        'SSLV3_ALERT_ILLEGAL_PARAMETER'
    ,
    (
        20,
        1048,
    ): 
        'TLSV1_ALERT_UNKNOWN_CA'
    ,
    (
        20,
        1049,
    ): 
        'TLSV1_ALERT_ACCESS_DENIED'
    ,
    (
        20,
        1050,
    ): 
        'TLSV1_ALERT_DECODE_ERROR'
    ,
    (
        20,
        1051,
    ): 
        'TLSV1_ALERT_DECRYPT_ERROR'
    ,
    (
        20,
        1060,
    ): 
        'TLSV1_ALERT_EXPORT_RESTRICTION'
    ,
    (
        20,
        1070,
    ): 
        'TLSV1_ALERT_PROTOCOL_VERSION'
    ,
    (
        20,
        1071,
    ): 
        'TLSV1_ALERT_INSUFFICIENT_SECURITY'
    ,
    (
        20,
        1080,
    ): 
        'TLSV1_ALERT_INTERNAL_ERROR'
    ,
    (
        20,
        1086,
    ): 
        'TLSV1_ALERT_INAPPROPRIATE_FALLBACK'
    ,
    (
        20,
        1090,
    ): 
        'TLSV1_ALERT_USER_CANCELLED'
    ,
    (
        20,
        1100,
    ): 
        'TLSV1_ALERT_NO_RENEGOTIATION'
    ,
    (
        20,
        1110,
    ): 
        'TLSV1_UNSUPPORTED_EXTENSION'
    ,
    (
        20,
        1111,
    ): 
        'TLSV1_CERTIFICATE_UNOBTAINABLE'
    ,
    (
        20,
        1112,
    ): 
        'TLSV1_UNRECOGNIZED_NAME'
    ,
    (
        20,
        1113,
    ): 
        'TLSV1_BAD_CERTIFICATE_STATUS_RESPONSE'
    ,
    (
        20,
        1114,
    ): 
        'TLSV1_BAD_CERTIFICATE_HASH_VALUE'
    ,
}

err_names_to_codes = {
    'AKID_MISMATCH': (
        11,
        110,
    ),
    'APP_DATA_IN_HANDSHAKE': (
        20,
        100,
    ),
    'ATTEMPT_TO_REUSE_SESSION_IN_DIFFERENT_CONTEXT': (
        20,
        272,
    ),
    'BAD_ALERT_RECORD': (
        20,
        101,
    ),
    'BAD_AUTHENTICATION_TYPE': (
        20,
        102,
    ),
    'BAD_BASE64_DECODE': (
        9,
        100,
    ),
    'BAD_CHANGE_CIPHER_SPEC': (
        20,
        103,
    ),
    'BAD_CHECKSUM': (
        20,
        104,
    ),
    'BAD_DATA': (
        20,
        390,
    ),
    'BAD_DATA_RETURNED_BY_CALLBACK': (
        20,
        106,
    ),
    'BAD_DECOMPRESSION': (
        20,
        107,
    ),
    'BAD_DECRYPT': (
        9,
        101,
    ),
    'BAD_DH_G_LENGTH': (
        20,
        108,
    ),
    'BAD_DH_PUB_KEY_LENGTH': (
        20,
        109,
    ),
    'BAD_DH_P_LENGTH': (
        20,
        110,
    ),
    'BAD_DIGEST_LENGTH': (
        20,
        111,
    ),
    'BAD_DSA_SIGNATURE': (
        20,
        112,
    ),
    'BAD_ECC_CERT': (
        20,
        304,
    ),
    'BAD_ECDSA_SIGNATURE': (
        20,
        305,
    ),
    'BAD_ECPOINT': (
        20,
        306,
    ),
    'BAD_END_LINE': (
        9,
        102,
    ),
    'BAD_HANDSHAKE_LENGTH': (
        20,
        332,
    ),
    'BAD_HELLO_REQUEST': (
        20,
        105,
    ),
    'BAD_IV_CHARS': (
        9,
        103,
    ),
    'BAD_LENGTH': (
        20,
        271,
    ),
    'BAD_MAC_DECODE': (
        20,
        113,
    ),
    'BAD_MAC_LENGTH': (
        20,
        333,
    ),
    'BAD_MAGIC_NUMBER': (
        9,
        116,
    ),
    'BAD_MESSAGE_TYPE': (
        20,
        114,
    ),
    'BAD_PACKET_LENGTH': (
        20,
        115,
    ),
    'BAD_PASSWORD_READ': (
        9,
        104,
    ),
    'BAD_PROTOCOL_VERSION_NUMBER': (
        20,
        116,
    ),
    'BAD_PSK_IDENTITY_HINT_LENGTH': (
        20,
        316,
    ),
    'BAD_RESPONSE_ARGUMENT': (
        20,
        117,
    ),
    'BAD_RSA_DECRYPT': (
        20,
        118,
    ),
    'BAD_RSA_ENCRYPT': (
        20,
        119,
    ),
    'BAD_RSA_E_LENGTH': (
        20,
        120,
    ),
    'BAD_RSA_MODULUS_LENGTH': (
        20,
        121,
    ),
    'BAD_RSA_SIGNATURE': (
        20,
        122,
    ),
    'BAD_SIGNATURE': (
        20,
        123,
    ),
    'BAD_SRP_A_LENGTH': (
        20,
        347,
    ),
    'BAD_SRP_B_LENGTH': (
        20,
        348,
    ),
    'BAD_SRP_G_LENGTH': (
        20,
        349,
    ),
    'BAD_SRP_N_LENGTH': (
        20,
        350,
    ),
    'BAD_SRP_PARAMETERS': (
        20,
        371,
    ),
    'BAD_SRP_S_LENGTH': (
        20,
        351,
    ),
    'BAD_SRTP_MKI_VALUE': (
        20,
        352,
    ),
    'BAD_SRTP_PROTECTION_PROFILE_LIST': (
        20,
        353,
    ),
    'BAD_SSL_FILETYPE': (
        20,
        124,
    ),
    'BAD_SSL_SESSION_ID_LENGTH': (
        20,
        125,
    ),
    'BAD_STATE': (
        20,
        126,
    ),
    'BAD_VALUE': (
        20,
        384,
    ),
    'BAD_VERSION_NUMBER': (
        9,
        117,
    ),
    'BAD_WRITE_RETRY': (
        20,
        127,
    ),
    'BAD_X509_FILETYPE': (
        11,
        100,
    ),
    'BASE64_DECODE_ERROR': (
        11,
        118,
    ),
    'BIO_NOT_SET': (
        20,
        128,
    ),
    'BIO_WRITE_FAILURE': (
        9,
        118,
    ),
    'BLOCK_CIPHER_PAD_IS_WRONG': (
        20,
        129,
    ),
    'BN_LIB': (
        20,
        130,
    ),
    'CANT_CHECK_DH_KEY': (
        11,
        114,
    ),
    'CA_DN_LENGTH_MISMATCH': (
        20,
        131,
    ),
    'CA_DN_TOO_LONG': (
        20,
        132,
    ),
    'CA_KEY_TOO_SMALL': (
        20,
        397,
    ),
    'CA_MD_TOO_WEAK': (
        20,
        398,
    ),
    'CCS_RECEIVED_EARLY': (
        20,
        133,
    ),
    'CERTIFICATE_VERIFY_FAILED': (
        20,
        134,
    ),
    'CERT_ALREADY_IN_HASH_TABLE': (
        11,
        101,
    ),
    'CERT_CB_ERROR': (
        20,
        377,
    ),
    'CERT_LENGTH_MISMATCH': (
        20,
        135,
    ),
    'CHALLENGE_IS_DIFFERENT': (
        20,
        136,
    ),
    'CIPHER_CODE_WRONG_LENGTH': (
        20,
        137,
    ),
    'CIPHER_IS_NULL': (
        9,
        127,
    ),
    'CIPHER_OR_HASH_UNAVAILABLE': (
        20,
        138,
    ),
    'CIPHER_TABLE_SRC_ERROR': (
        20,
        139,
    ),
    'CLIENTHELLO_TLSEXT': (
        20,
        226,
    ),
    'COMPRESSED_LENGTH_TOO_LONG': (
        20,
        140,
    ),
    'COMPRESSION_DISABLED': (
        20,
        343,
    ),
    'COMPRESSION_FAILURE': (
        20,
        141,
    ),
    'COMPRESSION_ID_NOT_WITHIN_PRIVATE_RANGE': (
        20,
        307,
    ),
    'COMPRESSION_LIBRARY_ERROR': (
        20,
        142,
    ),
    'CONNECTION_ID_IS_DIFFERENT': (
        20,
        143,
    ),
    'CONNECTION_TYPE_NOT_SET': (
        20,
        144,
    ),
    'COOKIE_MISMATCH': (
        20,
        308,
    ),
    'CRL_ALREADY_DELTA': (
        11,
        127,
    ),
    'CRL_VERIFY_FAILURE': (
        11,
        131,
    ),
    'DATA_BETWEEN_CCS_AND_FINISHED': (
        20,
        145,
    ),
    'DATA_LENGTH_TOO_LONG': (
        20,
        146,
    ),
    'DECRYPTION_FAILED': (
        20,
        147,
    ),
    'DECRYPTION_FAILED_OR_BAD_RECORD_MAC': (
        20,
        281,
    ),
    'DH_KEY_TOO_SMALL': (
        20,
        372,
    ),
    'DH_PUBLIC_VALUE_LENGTH_IS_WRONG': (
        20,
        148,
    ),
    'DIGEST_CHECK_FAILED': (
        20,
        149,
    ),
    'DTLS_MESSAGE_TOO_BIG': (
        20,
        334,
    ),
    'DUPLICATE_COMPRESSION_ID': (
        20,
        309,
    ),
    'ECC_CERT_NOT_FOR_KEY_AGREEMENT': (
        20,
        317,
    ),
    'ECC_CERT_NOT_FOR_SIGNING': (
        20,
        318,
    ),
    'ECC_CERT_SHOULD_HAVE_RSA_SIGNATURE': (
        20,
        322,
    ),
    'ECC_CERT_SHOULD_HAVE_SHA1_SIGNATURE': (
        20,
        323,
    ),
    'ECDH_REQUIRED_FOR_SUITEB_MODE': (
        20,
        374,
    ),
    'ECGROUP_TOO_LARGE_FOR_CIPHER': (
        20,
        310,
    ),
    'EE_KEY_TOO_SMALL': (
        20,
        399,
    ),
    'EMPTY_SRTP_PROTECTION_PROFILE_LIST': (
        20,
        354,
    ),
    'ENCRYPTED_LENGTH_TOO_LONG': (
        20,
        150,
    ),
    'ERROR_CONVERTING_PRIVATE_KEY': (
        9,
        115,
    ),
    'ERROR_GENERATING_TMP_RSA_KEY': (
        20,
        282,
    ),
    'ERROR_IN_RECEIVED_CIPHER_LIST': (
        20,
        151,
    ),
    'ERR_ASN1_LIB': (
        11,
        102,
    ),
    'EXCESSIVE_MESSAGE_SIZE': (
        20,
        152,
    ),
    'EXPECTING_PRIVATE_KEY_BLOB': (
        9,
        119,
    ),
    'EXPECTING_PUBLIC_KEY_BLOB': (
        9,
        120,
    ),
    'EXTRA_DATA_IN_MESSAGE': (
        20,
        153,
    ),
    'GOT_A_FIN_BEFORE_A_CCS': (
        20,
        154,
    ),
    'GOT_NEXT_PROTO_BEFORE_A_CCS': (
        20,
        355,
    ),
    'GOT_NEXT_PROTO_WITHOUT_EXTENSION': (
        20,
        356,
    ),
    'HTTPS_PROXY_REQUEST': (
        20,
        155,
    ),
    'HTTP_REQUEST': (
        20,
        156,
    ),
    'IDP_MISMATCH': (
        11,
        128,
    ),
    'ILLEGAL_PADDING': (
        20,
        283,
    ),
    'ILLEGAL_SUITEB_DIGEST': (
        20,
        380,
    ),
    'INAPPROPRIATE_FALLBACK': (
        20,
        373,
    ),
    'INCONSISTENT_COMPRESSION': (
        20,
        340,
    ),
    'INCONSISTENT_HEADER': (
        9,
        121,
    ),
    'INVALID_CHALLENGE_LENGTH': (
        20,
        158,
    ),
    'INVALID_COMMAND': (
        20,
        280,
    ),
    'INVALID_COMPRESSION_ALGORITHM': (
        20,
        341,
    ),
    'INVALID_DIRECTORY': (
        11,
        113,
    ),
    'INVALID_FIELD_NAME': (
        11,
        119,
    ),
    'INVALID_NULL_CMD_NAME': (
        20,
        385,
    ),
    'INVALID_PURPOSE': (
        20,
        278,
    ),
    'INVALID_SERVERINFO_DATA': (
        20,
        388,
    ),
    'INVALID_SRP_USERNAME': (
        20,
        357,
    ),
    'INVALID_STATUS_RESPONSE': (
        20,
        328,
    ),
    'INVALID_TICKET_KEYS_LENGTH': (
        20,
        325,
    ),
    'INVALID_TRUST': (
        11,
        123,
    ),
    'ISSUER_MISMATCH': (
        11,
        129,
    ),
    'KEYBLOB_HEADER_PARSE_ERROR': (
        9,
        122,
    ),
    'KEYBLOB_TOO_SHORT': (
        9,
        123,
    ),
    'KEY_ARG_TOO_LONG': (
        20,
        284,
    ),
    'KEY_TYPE_MISMATCH': (
        11,
        115,
    ),
    'KEY_VALUES_MISMATCH': (
        11,
        116,
    ),
    'KRB5': (
        20,
        285,
    ),
    'KRB5_C_CC_PRINC': (
        20,
        286,
    ),
    'KRB5_C_GET_CRED': (
        20,
        287,
    ),
    'KRB5_C_INIT': (
        20,
        288,
    ),
    'KRB5_C_MK_REQ': (
        20,
        289,
    ),
    'KRB5_S_BAD_TICKET': (
        20,
        290,
    ),
    'KRB5_S_INIT': (
        20,
        291,
    ),
    'KRB5_S_RD_REQ': (
        20,
        292,
    ),
    'KRB5_S_TKT_EXPIRED': (
        20,
        293,
    ),
    'KRB5_S_TKT_NYV': (
        20,
        294,
    ),
    'KRB5_S_TKT_SKEW': (
        20,
        295,
    ),
    'LENGTH_MISMATCH': (
        20,
        159,
    ),
    'LENGTH_TOO_SHORT': (
        20,
        160,
    ),
    'LIBRARY_BUG': (
        20,
        274,
    ),
    'LIBRARY_HAS_NO_CIPHERS': (
        20,
        161,
    ),
    'LOADING_CERT_DIR': (
        11,
        103,
    ),
    'LOADING_DEFAULTS': (
        11,
        104,
    ),
    'MESSAGE_TOO_LONG': (
        20,
        296,
    ),
    'METHOD_NOT_SUPPORTED': (
        11,
        124,
    ),
    'MISSING_DH_DSA_CERT': (
        20,
        162,
    ),
    'MISSING_DH_KEY': (
        20,
        163,
    ),
    'MISSING_DH_RSA_CERT': (
        20,
        164,
    ),
    'MISSING_DSA_SIGNING_CERT': (
        20,
        165,
    ),
    'MISSING_ECDH_CERT': (
        20,
        382,
    ),
    'MISSING_ECDSA_SIGNING_CERT': (
        20,
        381,
    ),
    'MISSING_EXPORT_TMP_DH_KEY': (
        20,
        166,
    ),
    'MISSING_EXPORT_TMP_RSA_KEY': (
        20,
        167,
    ),
    'MISSING_RSA_CERTIFICATE': (
        20,
        168,
    ),
    'MISSING_RSA_ENCRYPTING_CERT': (
        20,
        169,
    ),
    'MISSING_RSA_SIGNING_CERT': (
        20,
        170,
    ),
    'MISSING_SRP_PARAM': (
        20,
        358,
    ),
    'MISSING_TMP_DH_KEY': (
        20,
        171,
    ),
    'MISSING_TMP_ECDH_KEY': (
        20,
        311,
    ),
    'MISSING_TMP_RSA_KEY': (
        20,
        172,
    ),
    'MISSING_TMP_RSA_PKEY': (
        20,
        173,
    ),
    'MISSING_VERIFY_MESSAGE': (
        20,
        174,
    ),
    'MULTIPLE_SGC_RESTARTS': (
        20,
        346,
    ),
    'NEWER_CRL_NOT_NEWER': (
        11,
        132,
    ),
    'NON_SSLV2_INITIAL_PACKET': (
        20,
        175,
    ),
    'NOT_DEK_INFO': (
        9,
        105,
    ),
    'NOT_ENCRYPTED': (
        9,
        106,
    ),
    'NOT_PROC_TYPE': (
        9,
        107,
    ),
    'NO_CERTIFICATES_RETURNED': (
        20,
        176,
    ),
    'NO_CERTIFICATE_ASSIGNED': (
        20,
        177,
    ),
    'NO_CERTIFICATE_RETURNED': (
        20,
        178,
    ),
    'NO_CERTIFICATE_SET': (
        20,
        179,
    ),
    'NO_CERTIFICATE_SPECIFIED': (
        20,
        180,
    ),
    'NO_CERT_SET_FOR_US_TO_VERIFY': (
        11,
        105,
    ),
    'NO_CIPHERS_AVAILABLE': (
        20,
        181,
    ),
    'NO_CIPHERS_PASSED': (
        20,
        182,
    ),
    'NO_CIPHERS_SPECIFIED': (
        20,
        183,
    ),
    'NO_CIPHER_LIST': (
        20,
        184,
    ),
    'NO_CIPHER_MATCH': (
        20,
        185,
    ),
    'NO_CLIENT_CERT_METHOD': (
        20,
        331,
    ),
    'NO_CLIENT_CERT_RECEIVED': (
        20,
        186,
    ),
    'NO_COMPRESSION_SPECIFIED': (
        20,
        187,
    ),
    'NO_CRL_NUMBER': (
        11,
        130,
    ),
    'NO_GOST_CERTIFICATE_SENT_BY_PEER': (
        20,
        330,
    ),
    'NO_METHOD_SPECIFIED': (
        20,
        188,
    ),
    'NO_PEM_EXTENSIONS': (
        20,
        389,
    ),
    'NO_PRIVATEKEY': (
        20,
        189,
    ),
    'NO_PRIVATE_KEY_ASSIGNED': (
        20,
        190,
    ),
    'NO_PROTOCOLS_AVAILABLE': (
        20,
        191,
    ),
    'NO_PUBLICKEY': (
        20,
        192,
    ),
    'NO_RENEGOTIATION': (
        20,
        339,
    ),
    'NO_REQUIRED_DIGEST': (
        20,
        324,
    ),
    'NO_SHARED_CIPHER': (
        20,
        193,
    ),
    'NO_SHARED_SIGATURE_ALGORITHMS': (
        20,
        376,
    ),
    'NO_SRTP_PROFILES': (
        20,
        359,
    ),
    'NO_START_LINE': (
        9,
        108,
    ),
    'NO_VERIFY_CALLBACK': (
        20,
        194,
    ),
    'NULL_SSL_CTX': (
        20,
        195,
    ),
    'NULL_SSL_METHOD_PASSED': (
        20,
        196,
    ),
    'OLD_SESSION_CIPHER_NOT_RETURNED': (
        20,
        197,
    ),
    'OLD_SESSION_COMPRESSION_ALGORITHM_NOT_RETURNED': (
        20,
        344,
    ),
    'ONLY_DTLS_1_2_ALLOWED_IN_SUITEB_MODE': (
        20,
        387,
    ),
    'ONLY_TLS_1_2_ALLOWED_IN_SUITEB_MODE': (
        20,
        379,
    ),
    'ONLY_TLS_ALLOWED_IN_FIPS_MODE': (
        20,
        297,
    ),
    'OPAQUE_PRF_INPUT_TOO_LONG': (
        20,
        327,
    ),
    'PACKET_LENGTH_TOO_LONG': (
        20,
        198,
    ),
    'PARSE_TLSEXT': (
        20,
        227,
    ),
    'PATH_TOO_LONG': (
        20,
        270,
    ),
    'PEER_DID_NOT_RETURN_A_CERTIFICATE': (
        20,
        199,
    ),
    'PEER_ERROR': (
        20,
        200,
    ),
    'PEER_ERROR_CERTIFICATE': (
        20,
        201,
    ),
    'PEER_ERROR_NO_CERTIFICATE': (
        20,
        202,
    ),
    'PEER_ERROR_NO_CIPHER': (
        20,
        203,
    ),
    'PEER_ERROR_UNSUPPORTED_CERTIFICATE_TYPE': (
        20,
        204,
    ),
    'PEM_NAME_BAD_PREFIX': (
        20,
        391,
    ),
    'PEM_NAME_TOO_SHORT': (
        20,
        392,
    ),
    'PRE_MAC_LENGTH_TOO_LONG': (
        20,
        205,
    ),
    'PROBLEMS_GETTING_PASSWORD': (
        9,
        109,
    ),
    'PROBLEMS_MAPPING_CIPHER_FUNCTIONS': (
        20,
        206,
    ),
    'PROTOCOL_IS_SHUTDOWN': (
        20,
        207,
    ),
    'PSK_IDENTITY_NOT_FOUND': (
        20,
        223,
    ),
    'PSK_NO_CLIENT_CB': (
        20,
        224,
    ),
    'PSK_NO_SERVER_CB': (
        20,
        225,
    ),
    'PUBLIC_KEY_DECODE_ERROR': (
        11,
        125,
    ),
    'PUBLIC_KEY_ENCODE_ERROR': (
        11,
        126,
    ),
    'PUBLIC_KEY_ENCRYPT_ERROR': (
        20,
        208,
    ),
    'PUBLIC_KEY_IS_NOT_RSA': (
        20,
        209,
    ),
    'PUBLIC_KEY_NOT_RSA': (
        20,
        210,
    ),
    'PUBLIC_KEY_NO_RSA': (
        9,
        110,
    ),
    'PVK_DATA_TOO_SHORT': (
        9,
        124,
    ),
    'PVK_TOO_SHORT': (
        9,
        125,
    ),
    'READ_BIO_NOT_SET': (
        20,
        211,
    ),
    'READ_KEY': (
        9,
        111,
    ),
    'READ_TIMEOUT_EXPIRED': (
        20,
        312,
    ),
    'READ_WRONG_PACKET_TYPE': (
        20,
        212,
    ),
    'RECORD_LENGTH_MISMATCH': (
        20,
        213,
    ),
    'RECORD_TOO_LARGE': (
        20,
        214,
    ),
    'RECORD_TOO_SMALL': (
        20,
        298,
    ),
    'RENEGOTIATE_EXT_TOO_LONG': (
        20,
        335,
    ),
    'RENEGOTIATION_ENCODING_ERR': (
        20,
        336,
    ),
    'RENEGOTIATION_MISMATCH': (
        20,
        337,
    ),
    'REQUIRED_CIPHER_MISSING': (
        20,
        215,
    ),
    'REQUIRED_COMPRESSSION_ALGORITHM_MISSING': (
        20,
        342,
    ),
    'REUSE_CERT_LENGTH_NOT_ZERO': (
        20,
        216,
    ),
    'REUSE_CERT_TYPE_NOT_ZERO': (
        20,
        217,
    ),
    'REUSE_CIPHER_LIST_NOT_ZERO': (
        20,
        218,
    ),
    'SCSV_RECEIVED_WHEN_RENEGOTIATING': (
        20,
        345,
    ),
    'SERVERHELLO_TLSEXT': (
        20,
        275,
    ),
    'SESSION_ID_CONTEXT_UNINITIALIZED': (
        20,
        277,
    ),
    'SHORT_HEADER': (
        9,
        112,
    ),
    'SHORT_READ': (
        20,
        219,
    ),
    'SHOULD_RETRY': (
        11,
        106,
    ),
    'SIGNATURE_ALGORITHMS_ERROR': (
        20,
        360,
    ),
    'SIGNATURE_FOR_NON_SIGNING_CERTIFICATE': (
        20,
        220,
    ),
    'SRP_A_CALC': (
        20,
        361,
    ),
    'SRTP_COULD_NOT_ALLOCATE_PROFILES': (
        20,
        362,
    ),
    'SRTP_PROTECTION_PROFILE_LIST_TOO_LONG': (
        20,
        363,
    ),
    'SRTP_UNKNOWN_PROTECTION_PROFILE': (
        20,
        364,
    ),
    'SSL23_DOING_SESSION_ID_REUSE': (
        20,
        221,
    ),
    'SSL2_CONNECTION_ID_TOO_LONG': (
        20,
        299,
    ),
    'SSL3_EXT_INVALID_ECPOINTFORMAT': (
        20,
        321,
    ),
    'SSL3_EXT_INVALID_SERVERNAME': (
        20,
        319,
    ),
    'SSL3_EXT_INVALID_SERVERNAME_TYPE': (
        20,
        320,
    ),
    'SSL3_SESSION_ID_TOO_LONG': (
        20,
        300,
    ),
    'SSL3_SESSION_ID_TOO_SHORT': (
        20,
        222,
    ),
    'SSLV3_ALERT_BAD_CERTIFICATE': (
        20,
        1042,
    ),
    'SSLV3_ALERT_BAD_RECORD_MAC': (
        20,
        1020,
    ),
    'SSLV3_ALERT_CERTIFICATE_EXPIRED': (
        20,
        1045,
    ),
    'SSLV3_ALERT_CERTIFICATE_REVOKED': (
        20,
        1044,
    ),
    'SSLV3_ALERT_CERTIFICATE_UNKNOWN': (
        20,
        1046,
    ),
    'SSLV3_ALERT_DECOMPRESSION_FAILURE': (
        20,
        1030,
    ),
    'SSLV3_ALERT_HANDSHAKE_FAILURE': (
        20,
        1040,
    ),
    'SSLV3_ALERT_ILLEGAL_PARAMETER': (
        20,
        1047,
    ),
    'SSLV3_ALERT_NO_CERTIFICATE': (
        20,
        1041,
    ),
    'SSLV3_ALERT_UNEXPECTED_MESSAGE': (
        20,
        1010,
    ),
    'SSLV3_ALERT_UNSUPPORTED_CERTIFICATE': (
        20,
        1043,
    ),
    'SSL_CTX_HAS_NO_DEFAULT_SSL_VERSION': (
        20,
        228,
    ),
    'SSL_HANDSHAKE_FAILURE': (
        20,
        229,
    ),
    'SSL_LIBRARY_HAS_NO_CIPHERS': (
        20,
        230,
    ),
    'SSL_NEGATIVE_LENGTH': '<value is a self-reference, replaced by this string>',
    'SSL_SESSION_ID_CALLBACK_FAILED': (
        20,
        301,
    ),
    'SSL_SESSION_ID_CONFLICT': (
        20,
        302,
    ),
    'SSL_SESSION_ID_CONTEXT_TOO_LONG': (
        20,
        273,
    ),
    'SSL_SESSION_ID_HAS_BAD_LENGTH': (
        20,
        303,
    ),
    'SSL_SESSION_ID_IS_DIFFERENT': (
        20,
        231,
    ),
    'TLSV1_ALERT_ACCESS_DENIED': (
        20,
        1049,
    ),
    'TLSV1_ALERT_DECODE_ERROR': (
        20,
        1050,
    ),
    'TLSV1_ALERT_DECRYPTION_FAILED': (
        20,
        1021,
    ),
    'TLSV1_ALERT_DECRYPT_ERROR': (
        20,
        1051,
    ),
    'TLSV1_ALERT_EXPORT_RESTRICTION': (
        20,
        1060,
    ),
    'TLSV1_ALERT_INAPPROPRIATE_FALLBACK': (
        20,
        1086,
    ),
    'TLSV1_ALERT_INSUFFICIENT_SECURITY': (
        20,
        1071,
    ),
    'TLSV1_ALERT_INTERNAL_ERROR': (
        20,
        1080,
    ),
    'TLSV1_ALERT_NO_RENEGOTIATION': (
        20,
        1100,
    ),
    'TLSV1_ALERT_PROTOCOL_VERSION': (
        20,
        1070,
    ),
    'TLSV1_ALERT_RECORD_OVERFLOW': (
        20,
        1022,
    ),
    'TLSV1_ALERT_UNKNOWN_CA': (
        20,
        1048,
    ),
    'TLSV1_ALERT_USER_CANCELLED': (
        20,
        1090,
    ),
    'TLSV1_BAD_CERTIFICATE_HASH_VALUE': (
        20,
        1114,
    ),
    'TLSV1_BAD_CERTIFICATE_STATUS_RESPONSE': (
        20,
        1113,
    ),
    'TLSV1_CERTIFICATE_UNOBTAINABLE': (
        20,
        1111,
    ),
    'TLSV1_UNRECOGNIZED_NAME': (
        20,
        1112,
    ),
    'TLSV1_UNSUPPORTED_EXTENSION': (
        20,
        1110,
    ),
    'TLS_CLIENT_CERT_REQ_WITH_ANON_CIPHER': (
        20,
        232,
    ),
    'TLS_HEARTBEAT_PEER_DOESNT_ACCEPT': (
        20,
        365,
    ),
    'TLS_HEARTBEAT_PENDING': (
        20,
        366,
    ),
    'TLS_ILLEGAL_EXPORTER_LABEL': (
        20,
        367,
    ),
    'TLS_INVALID_ECPOINTFORMAT_LIST': (
        20,
        157,
    ),
    'TLS_PEER_DID_NOT_RESPOND_WITH_CERTIFICATE_LIST': (
        20,
        233,
    ),
    'TLS_RSA_ENCRYPTED_VALUE_LENGTH_IS_WRONG': (
        20,
        234,
    ),
    'TRIED_TO_USE_UNSUPPORTED_CIPHER': (
        20,
        235,
    ),
    'UNABLE_TO_DECODE_DH_CERTS': (
        20,
        236,
    ),
    'UNABLE_TO_DECODE_ECDH_CERTS': (
        20,
        313,
    ),
    'UNABLE_TO_EXTRACT_PUBLIC_KEY': (
        20,
        237,
    ),
    'UNABLE_TO_FIND_DH_PARAMETERS': (
        20,
        238,
    ),
    'UNABLE_TO_FIND_ECDH_PARAMETERS': (
        20,
        314,
    ),
    'UNABLE_TO_FIND_PARAMETERS_IN_CHAIN': (
        11,
        107,
    ),
    'UNABLE_TO_FIND_PUBLIC_KEY_PARAMETERS': (
        20,
        239,
    ),
    'UNABLE_TO_FIND_SSL_METHOD': (
        20,
        240,
    ),
    'UNABLE_TO_GET_CERTS_PUBLIC_KEY': (
        11,
        108,
    ),
    'UNABLE_TO_LOAD_SSL2_MD5_ROUTINES': (
        20,
        241,
    ),
    'UNABLE_TO_LOAD_SSL3_MD5_ROUTINES': (
        20,
        242,
    ),
    'UNABLE_TO_LOAD_SSL3_SHA1_ROUTINES': (
        20,
        243,
    ),
    'UNEXPECTED_MESSAGE': (
        20,
        244,
    ),
    'UNEXPECTED_RECORD': (
        20,
        245,
    ),
    'UNINITIALIZED': (
        20,
        276,
    ),
    'UNKNOWN_ALERT_TYPE': (
        20,
        246,
    ),
    'UNKNOWN_CERTIFICATE_TYPE': (
        20,
        247,
    ),
    'UNKNOWN_CIPHER_RETURNED': (
        20,
        248,
    ),
    'UNKNOWN_CIPHER_TYPE': (
        20,
        249,
    ),
    'UNKNOWN_CMD_NAME': (
        20,
        386,
    ),
    'UNKNOWN_DIGEST': (
        20,
        368,
    ),
    'UNKNOWN_KEY_EXCHANGE_TYPE': (
        20,
        250,
    ),
    'UNKNOWN_KEY_TYPE': (
        11,
        117,
    ),
    'UNKNOWN_NID': (
        11,
        109,
    ),
    'UNKNOWN_PKEY_TYPE': (
        20,
        251,
    ),
    'UNKNOWN_PROTOCOL': (
        20,
        252,
    ),
    'UNKNOWN_PURPOSE_ID': (
        11,
        121,
    ),
    'UNKNOWN_REMOTE_ERROR_TYPE': (
        20,
        253,
    ),
    'UNKNOWN_SSL_VERSION': (
        20,
        254,
    ),
    'UNKNOWN_STATE': (
        20,
        255,
    ),
    'UNKNOWN_TRUST_ID': (
        11,
        120,
    ),
    'UNSAFE_LEGACY_RENEGOTIATION_DISABLED': (
        20,
        338,
    ),
    'UNSUPPORTED_ALGORITHM': (
        11,
        111,
    ),
    'UNSUPPORTED_CIPHER': (
        20,
        256,
    ),
    'UNSUPPORTED_COMPRESSION_ALGORITHM': (
        20,
        257,
    ),
    'UNSUPPORTED_DIGEST_TYPE': (
        20,
        326,
    ),
    'UNSUPPORTED_ELLIPTIC_CURVE': (
        20,
        315,
    ),
    'UNSUPPORTED_ENCRYPTION': (
        9,
        114,
    ),
    'UNSUPPORTED_KEY_COMPONENTS': (
        9,
        126,
    ),
    'UNSUPPORTED_PROTOCOL': (
        20,
        258,
    ),
    'UNSUPPORTED_SSL_VERSION': (
        20,
        259,
    ),
    'UNSUPPORTED_STATUS_TYPE': (
        20,
        329,
    ),
    'USE_SRTP_NOT_NEGOTIATED': (
        20,
        369,
    ),
    'VERSION_TOO_LOW': (
        20,
        396,
    ),
    'WRITE_BIO_NOT_SET': (
        20,
        260,
    ),
    'WRONG_CERTIFICATE_TYPE': (
        20,
        383,
    ),
    'WRONG_CIPHER_RETURNED': (
        20,
        261,
    ),
    'WRONG_CURVE': (
        20,
        378,
    ),
    'WRONG_LOOKUP_TYPE': (
        11,
        112,
    ),
    'WRONG_MESSAGE_TYPE': (
        20,
        262,
    ),
    'WRONG_NUMBER_OF_KEY_BITS': (
        20,
        263,
    ),
    'WRONG_SIGNATURE_LENGTH': (
        20,
        264,
    ),
    'WRONG_SIGNATURE_SIZE': (
        20,
        265,
    ),
    'WRONG_SIGNATURE_TYPE': (
        20,
        370,
    ),
    'WRONG_SSL_VERSION': (
        20,
        266,
    ),
    'WRONG_TYPE': (
        11,
        122,
    ),
    'WRONG_VERSION_NUMBER': (
        20,
        267,
    ),
    'X509_LIB': (
        20,
        268,
    ),
    'X509_VERIFICATION_SETUP_PROBLEMS': (
        20,
        269,
    ),
}

lib_codes_to_names = {
    9: 'PEM',
    11: 'X509',
    20: 'SSL',
}

OPENSSL_VERSION_INFO = (
    1,
    0,
    1,
    20,
    15,
)

_OPENSSL_API_VERSION = (
    1,
    0,
    1,
    20,
    15,
)

__loader__ = None # (!) real value is ''

__spec__ = None # (!) real value is ''

