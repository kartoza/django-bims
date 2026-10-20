# coding=utf-8
"""Evaluate the saved filter of an OgcLayer into a record queryset.

The filter is run through the same CollectionSearch used by the BIMS
search page, then restricted so that a layer only ever exposes records
that are safe to serve behind a shared URL.
"""
import datetime
import hashlib
import json

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django.utils import timezone

from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)

# Search parameters that narrow the result set. A layer needs at least one,
# so that an unfiltered layer can never expose the whole dataset.
NARROWING_PARAMS = (
    'search',
    'taxon',
    'siteId',
    'months',
    'invasions',
    'category',
    'collector',
    'collectors',
    'reference',
    'referenceCategory',
    'conservationStatus',
    'dst',
    'boundary',
    'userBoundary',
    'endemic',
    'sourceCollection',
    'tags',
    'datasetKeys',
    'polygon',
    'modules',
    'mg',
    'ecosystemType',
    'spatialFilter',
    'asf',
)

# Search modules that do not return biological collection records
UNSUPPORTED_MODULES = ('water_temperature', 'physico_chemistry', 'climate')

SENSITIVE_GROUP = 'SensitiveDataGroup'
PRIVATE_GROUP = 'PrivateDataGroup'


class OgcLayerError(Exception):
    """Base class for layer evaluation errors."""


class OgcLayerFilterError(OgcLayerError):
    """The saved filter is empty, too broad or not supported."""


class OgcLayerOverCapError(OgcLayerError):
    """The filter matches more records than OGC_LAYER_MAX_RECORDS."""

    def __init__(self, cap):
        self.cap = cap
        super().__init__(
            'The filter matches more than %d records. '
            'Narrow the filter to publish it as a layer.' % cap
        )


def _is_empty(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in ('', '[]', '{}', 'null', 'false')
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def has_narrowing_filter(query):
    """Whether the query has at least one filter that narrows the results."""
    if not isinstance(query, dict):
        return False
    for param in NARROWING_PARAMS:
        if not _is_empty(query.get(param)):
            return True
    # The year range only narrows the results when both ends are given
    return (
        not _is_empty(query.get('yearFrom')) and
        not _is_empty(query.get('yearTo'))
    )


def validate_query(query):
    """Check that a saved filter can be served as a layer.

    :raises OgcLayerFilterError: if the filter is not allowed.
    """
    if not isinstance(query, dict):
        raise OgcLayerFilterError('The filter must be a JSON object.')
    if not has_narrowing_filter(query):
        raise OgcLayerFilterError(
            'Apply at least one filter, such as a taxon, site, year range, '
            'reference or area, before publishing a layer.'
        )
    if (
        query.get('module') in UNSUPPORTED_MODULES or
        not _is_empty(query.get('thermalModule'))
    ):
        raise OgcLayerFilterError(
            'Only occurrence records can be published as a layer.'
        )


def _search_parameters(layer):
    parameters = {
        key: value for key, value in layer.query.items()
        if key != 'requester'
    }
    return parameters


def _allowed_data_types(layer):
    """Data types the layer may expose.

    Sensitive and private records need both the layer opting in and the
    owner belonging to the matching group.
    """
    group_names = set(layer.owner.groups.values_list('name', flat=True))
    data_types = ['public']
    if layer.include_sensitive and SENSITIVE_GROUP in group_names:
        data_types.append('sensitive')
    if layer.include_private and PRIVATE_GROUP in group_names:
        data_types.append('private')
    return data_types


def get_layer_queryset(layer):
    """Return the records a layer serves, as a queryset ordered by id.

    The saved filter is evaluated as the layer owner. On top of that the
    layer only serves validated records that are not under embargo, even
    when they belong to the owner, and only the data types allowed for it.
    """
    from bims.api_views.search import CollectionSearch

    validate_query(layer.query)
    if not layer.owner.is_active:
        return BiologicalCollectionRecord.objects.none()

    search = CollectionSearch(
        _search_parameters(layer),
        requester_id=layer.owner_id
    )
    if search.is_sass_records_only():
        raise OgcLayerFilterError(
            'SASS filters are not supported for layers.'
        )
    matched = search.process_search()

    today = datetime.date.today()
    # Select by id so that joins in the filter cannot return a record twice
    return BiologicalCollectionRecord.objects.filter(
        pk__in=matched.order_by().values('pk'),
        validated=True
    ).filter(
        Q(end_embargo_date__isnull=True) |
        Q(end_embargo_date__lte=today) |
        Q(start_embargo_date__gt=today)
    ).filter(
        Q(data_type='') |
        Q(data_type__in=_allowed_data_types(layer))
    ).order_by('pk')


def _count_cache_key(layer):
    digest = hashlib.sha256(json.dumps({
        'query': layer.query,
        'owner': layer.owner_id,
        'sensitive': layer.include_sensitive,
        'private': layer.include_private,
    }, sort_keys=True, default=str).encode('utf-8')).hexdigest()
    return 'ogc_layer_count:%s:%s:%s' % (
        connection.schema_name, layer.pk, digest)


def count_layer_records(layer, use_cache=True):
    """Count the records of a layer, never counting beyond the cap.

    The count is cached for OGC_LAYER_COUNT_CACHE_TTL seconds so paging
    through a layer does not repeat the search for every page.

    :raises OgcLayerOverCapError: if the layer has more records than
        OGC_LAYER_MAX_RECORDS.
    :return: number of records, at most OGC_LAYER_MAX_RECORDS.
    """
    cap = settings.OGC_LAYER_MAX_RECORDS
    cache_key = _count_cache_key(layer)
    count = cache.get(cache_key) if use_cache else None
    if count is None:
        # Counting one record past the cap is enough to know it is exceeded
        count = get_layer_queryset(layer).values('pk')[:cap + 1].count()
        cache.set(cache_key, count, settings.OGC_LAYER_COUNT_CACHE_TTL)
        if count <= cap and layer.pk:
            now = timezone.now()
            type(layer).objects.filter(pk=layer.pk).update(
                record_count_cached=count,
                record_count_updated=now
            )
            layer.record_count_cached = count
            layer.record_count_updated = now
    if count > cap:
        raise OgcLayerOverCapError(cap)
    return count


def validate_layer(layer):
    """Check a layer can be published and return its record count.

    :raises OgcLayerError: if the filter is not allowed or matches more
        than OGC_LAYER_MAX_RECORDS records.
    """
    validate_query(layer.query)
    return count_layer_records(layer, use_cache=False)
