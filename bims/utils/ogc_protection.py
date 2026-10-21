# coding=utf-8
"""Keep OGC layers from overloading the shared database.

- statement_timeout(): runs queries under a Postgres statement timeout.
- single_flight(): lets one request at a time build a cached value, with a
  cap on how many layers are evaluated at once.
- check_rate(): fixed-window rate limits, kept in the cache.

All counters live in the cache, which is shared by the workers of a tenant.
If the cache is unavailable the limits fail open, so a cache outage does not
take the layers down.
"""
import logging
import time
from contextlib import contextmanager

from django.conf import settings
from django.core.cache import cache
from django.db import OperationalError, connection, transaction

logger = logging.getLogger(__name__)

# SQLSTATE query_canceled, raised when statement_timeout expires
QUERY_CANCELED = '57014'


class OgcLayerProtectionError(Exception):
    """Base class for errors that tell the client to back off."""

    retry_after = 5

    def __init__(self, message, retry_after=None):
        if retry_after is not None:
            self.retry_after = retry_after
        super().__init__(message)


class OgcLayerTimeoutError(OgcLayerProtectionError):
    """A query ran longer than OGC_LAYER_STATEMENT_TIMEOUT."""


class OgcLayerBusyError(OgcLayerProtectionError):
    """The layer is being evaluated, or too many layers are."""


class OgcLayerThrottledError(OgcLayerProtectionError):
    """A rate limit was exceeded."""


def _is_query_canceled(exc):
    cause = getattr(exc, '__cause__', None)
    return getattr(cause, 'pgcode', None) == QUERY_CANCELED


@contextmanager
def statement_timeout(seconds=None, avoid_index_scan=False):
    """Run the queries in the block under a statement timeout.

    Queries must be evaluated inside the block, not returned lazily.

    :param avoid_index_scan: also stop Postgres from choosing a plain index
        scan. For ``LIMIT`` queries on a huge table with few matches it can
        walk the primary key of the whole table, since it expects to find
        enough rows early. Bitmap and sequential scans are not affected.
    :raises OgcLayerTimeoutError: if a query was cancelled by the timeout.
    """
    seconds = (
        settings.OGC_LAYER_STATEMENT_TIMEOUT if seconds is None else seconds)
    local = {}
    if seconds:
        local['statement_timeout'] = str(int(seconds * 1000))
    if avoid_index_scan:
        local['enable_indexscan'] = 'off'
    if not local:
        yield
        return
    # SET LOCAL lasts until the end of the outermost transaction, so inside
    # a wider transaction the previous values are put back by hand
    previous = {}
    nested = connection.in_atomic_block
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                for name, value in local.items():
                    if nested:
                        cursor.execute('SHOW %s' % name)
                        previous[name] = cursor.fetchone()[0]
                    cursor.execute('SELECT set_config(%s, %s, true)',
                                   [name, value])
            yield
            if previous:
                with connection.cursor() as cursor:
                    for name, value in previous.items():
                        cursor.execute(
                            'SELECT set_config(%s, %s, true)', [name, value])
    except OperationalError as exc:
        if not _is_query_canceled(exc):
            raise
        raise OgcLayerTimeoutError(
            'The layer query took too long. Try again later or narrow '
            'the filter.',
            retry_after=settings.OGC_LAYER_RETRY_AFTER
        ) from exc


def _schema_key(*parts):
    return ':'.join(
        ['ogc_protect', connection.schema_name] + [str(p) for p in parts])


def _cache_call(func, default=None):
    try:
        return func()
    except Exception:
        logger.warning('OGC layer protection cache error', exc_info=True)
        return default


@contextmanager
def evaluation_slot():
    """Take one of the OGC_LAYER_MAX_CONCURRENT_EVALUATIONS slots.

    Waits up to OGC_LAYER_LOCK_WAIT seconds for a slot, since evaluations
    are short, before giving up.

    :raises OgcLayerBusyError: if all slots stay taken.
    """
    limit = settings.OGC_LAYER_MAX_CONCURRENT_EVALUATIONS
    key = _schema_key('slots')
    ttl = settings.OGC_LAYER_LOCK_TTL

    def acquire():
        cache.add(key, 0, ttl)
        return cache.incr(key)

    def release():
        _cache_call(lambda: cache.decr(key))

    deadline = time.monotonic() + settings.OGC_LAYER_LOCK_WAIT
    while True:
        taken = _cache_call(acquire)
        if taken is None or not limit or taken <= limit:
            break
        release()
        if time.monotonic() >= deadline:
            raise OgcLayerBusyError(
                'Too many layers are being prepared. Try again shortly.',
                retry_after=settings.OGC_LAYER_RETRY_AFTER)
        time.sleep(0.1)
    try:
        yield
    finally:
        if taken is not None:
            release()


def single_flight(name, read, build):
    """Return read(), building it with build() when it is missing.

    One request at a time builds a given ``name``. The others wait for up to
    OGC_LAYER_LOCK_WAIT seconds for the result, then give up.

    :param read: returns the cached value, or None.
    :param build: computes (and caches) the value. Run inside an
        evaluation slot.
    :raises OgcLayerBusyError: if the value is still being built after the
        wait, or all evaluation slots are taken.
    """
    value = read()
    if value is not None:
        return value
    lock_key = _schema_key('lock', name)
    deadline = time.monotonic() + settings.OGC_LAYER_LOCK_WAIT
    while True:
        locked = _cache_call(
            lambda: cache.add(lock_key, 1, settings.OGC_LAYER_LOCK_TTL),
            default=True)
        if locked:
            try:
                # Another request may have built it while we waited
                value = read()
                if value is not None:
                    return value
                with evaluation_slot():
                    return build()
            finally:
                _cache_call(lambda: cache.delete(lock_key))
        value = read()
        if value is not None:
            return value
        if time.monotonic() >= deadline:
            raise OgcLayerBusyError(
                'This layer is being prepared. Try again shortly.',
                retry_after=settings.OGC_LAYER_RETRY_AFTER)
        time.sleep(0.2)


def client_ip(request):
    """Client address, trusting OGC_TRUSTED_PROXIES proxies in front of us.

    The proxies append the address they saw to X-Forwarded-For, so the
    client is that many entries from the right. Earlier entries can be
    forged by the client and are ignored.
    """
    proxies = settings.OGC_TRUSTED_PROXIES
    forwarded = [
        part.strip()
        for part in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')
        if part.strip()
    ]
    if proxies and len(forwarded) >= proxies:
        return forwarded[-proxies]
    return request.META.get('REMOTE_ADDR') or 'unknown'


def check_rate(scope, identifier, limit, window=60, message=None):
    """Count a request and refuse it once ``limit`` is passed in the window.

    :raises OgcLayerThrottledError: when over the limit.
    """
    if not limit:
        return
    now = int(time.time())
    bucket = now // window
    key = _schema_key('rate', scope, identifier, bucket)

    def count():
        cache.add(key, 0, window + 5)
        return cache.incr(key)

    used = _cache_call(count)
    if used is not None and used > limit:
        raise OgcLayerThrottledError(
            message or 'Too many requests. Slow down and try again.',
            retry_after=window - (now % window) or 1)
