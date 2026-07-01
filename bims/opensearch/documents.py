import logging
from django.db import connection
from bims.opensearch.client import get_client
from bims.opensearch.indices import COLLECTIONS_INDEX

logger = logging.getLogger('bims')


def doc_id(schema_name: str, record_id: int) -> str:
    """Composite document ID that prevents collisions across tenant schemas."""
    return f'{schema_name}_{record_id}'


def build_document(record, schema_name: str) -> dict:
    """Build a flat OpenSearch document from a BiologicalCollectionRecord."""
    site = record.site
    taxonomy = record.taxonomy

    location = None
    if site and site.geometry_point:
        location = {
            'lat': site.geometry_point.y,
            'lon': site.geometry_point.x,
        }

    canonical_name = ''
    scientific_name = ''
    vernacular_names = []
    tags = []
    endemism = None
    conservation_status = None
    national_conservation_status = None
    origin = None
    taxonomy_id = None

    if taxonomy:
        taxonomy_id = taxonomy.id
        canonical_name = taxonomy.canonical_name or ''
        scientific_name = taxonomy.scientific_name or ''
        vernacular_names = list(
            taxonomy.vernacular_names.values_list('name', flat=True)
        )
        tags = list(taxonomy.tags.values_list('name', flat=True))
        endemism = taxonomy.endemism.name if taxonomy.endemism else None
        if hasattr(taxonomy, 'iucn_status') and taxonomy.iucn_status:
            conservation_status = taxonomy.iucn_status.category
        if hasattr(taxonomy, 'national_conservation_status') and taxonomy.national_conservation_status:
            national_conservation_status = taxonomy.national_conservation_status.category
        origin = (
            taxonomy.origin.origin_key
            if taxonomy.origin_id and taxonomy.origin
            else None
        )

    taxon_group_ids = []
    if taxonomy:
        taxon_group_ids = list(
            taxonomy.taxongroup_set.values_list('id', flat=True)
        )

    module_group_id = None
    module_group_name = None
    if record.module_group:
        module_group_id = record.module_group.id
        module_group_name = record.module_group.name

    site_id = None
    site_code = ''
    site_name = ''
    river_name = ''
    ecosystem_type = ''
    location_context_groups = []
    location_context_values = []
    if site:
        site_id = site.id
        site_code = site.site_code or ''
        site_name = site.name or ''
        if site.river:
            river_name = site.river.name or ''
        ecosystem_type = site.ecosystem_type or ''
        location_context_groups, location_context_values = (
            build_location_context_tokens(site)
        )

    end_embargo_date = None
    if record.end_embargo_date:
        end_embargo_date = record.end_embargo_date.strftime('%Y-%m-%d')

    sampling_method = None
    if record.sampling_method_id and record.sampling_method:
        sampling_method = record.sampling_method.sampling_method or None

    biotope = None
    if record.biotope_id and record.biotope:
        biotope = record.biotope.name or None

    taxonomy_rank = None
    taxonomy_status = None
    include_in_rli = False
    if taxonomy:
        taxonomy_rank = getattr(taxonomy, 'rank', None) or None
        taxonomy_status = getattr(taxonomy, 'taxonomic_status', None) or None
        include_in_rli = bool(getattr(taxonomy, 'include_in_rli', False))

    return {
        'schema_name': schema_name,
        'record_id': record.id,
        'uuid': str(record.uuid) if record.uuid else None,
        'taxonomy_id': taxonomy_id,
        'canonical_name': canonical_name,
        'scientific_name': scientific_name,
        'vernacular_names': vernacular_names,
        'tags': tags,
        'endemism': endemism,
        'conservation_status': conservation_status,
        'national_conservation_status': national_conservation_status,
        'origin': origin,
        'sampling_method': sampling_method,
        'biotope': biotope,
        'taxonomy_rank': taxonomy_rank,
        'taxonomy_status': taxonomy_status,
        'include_in_rli': include_in_rli,
        'module_group_id': module_group_id,
        'module_group_name': module_group_name,
        'taxon_group_ids': taxon_group_ids,
        'site_id': site_id,
        'site_code': site_code,
        'site_name': site_name,
        'river_name': river_name,
        'ecosystem_type': ecosystem_type,
        'location': location,
        'location_context_groups': location_context_groups,
        'location_context_values': location_context_values,
        'collection_date': (
            record.collection_date.strftime('%Y-%m-%d')
            if record.collection_date else None
        ),
        'collector': record.collector or '',
        'original_species_name': record.original_species_name or '',
        'data_type': record.data_type or 'public',
        'owner_id': record.owner_id,
        'is_validated': record.validated,
        'ready_for_validation': record.ready_for_validation,
        'end_embargo_date': end_embargo_date,
    }


def build_location_context_tokens(site) -> tuple:
    groups = set()
    values = set()

    for context in site.locationcontext_set.all():
        group = context.group
        if not group or not group.key:
            continue

        group_tokens = [group.key]
        if group.layer_identifier:
            group_tokens.append(f'{group.key}.{group.layer_identifier}')

        for token in group_tokens:
            groups.add(token)
            if context.value:
                values.add(f'{token}|{context.value}')

    return sorted(groups), sorted(values)


def index_record(record, schema_name: str = None):
    """Upsert a single BiologicalCollectionRecord into OpenSearch."""
    if schema_name is None:
        schema_name = connection.schema_name
    client = get_client()
    doc = build_document(record, schema_name)
    client.index(
        index=COLLECTIONS_INDEX,
        id=doc_id(schema_name, record.id),
        body=doc,
    )


def delete_record(record_id: int, schema_name: str = None):
    """Remove a record from the index."""
    if schema_name is None:
        schema_name = connection.schema_name
    client = get_client()
    try:
        client.delete(
            index=COLLECTIONS_INDEX,
            id=doc_id(schema_name, record_id),
            ignore=[404],
        )
    except Exception as exc:
        logger.warning(
            'Failed to delete record %s/%s from index: %s',
            schema_name, record_id, exc,
        )


def bulk_index(schema_name: str, chunk_size=500, on_progress=None) -> int:
    """
    Bulk-index all BiologicalCollectionRecords for a tenant schema.

    Uses manual ID-based chunking instead of .iterator() because Django's
    prefetch_related is silently ignored with .iterator(), which causes 3+
    extra queries per record (vernacular_names, tags, taxongroup_set).

    on_progress: optional callable(total_indexed_so_far) called after each chunk.
    """
    from opensearchpy.helpers import bulk
    from bims.models.biological_collection_record import BiologicalCollectionRecord

    client = get_client()
    total_ok = 0

    ids = list(
        BiologicalCollectionRecord.objects.values_list('id', flat=True).order_by('id')
    )

    for offset in range(0, len(ids), chunk_size):
        batch_ids = ids[offset:offset + chunk_size]
        batch = list(
            BiologicalCollectionRecord.objects.filter(id__in=batch_ids).select_related(
                'site__river',
                'taxonomy__endemism',
                'taxonomy__iucn_status',
                'taxonomy__national_conservation_status',
                'taxonomy__origin',
                'module_group',
                'owner',
                'sampling_method',
                'biotope',
            ).prefetch_related(
                'site__locationcontext_set__group',
                'taxonomy__tags',
                'taxonomy__vernacular_names',
                'taxonomy__taxongroup_set',
            )
        )

        actions = []
        for record in batch:
            doc = build_document(record, schema_name)
            doc['_index'] = COLLECTIONS_INDEX
            doc['_id'] = doc_id(schema_name, record.id)
            actions.append(doc)

        ok, errors = bulk(client, actions, raise_on_error=False)
        total_ok += ok
        if errors:
            logger.warning(
                '%d errors in chunk starting at offset %d for schema %s',
                len(errors), offset, schema_name,
            )
        if on_progress:
            on_progress(total_ok)

    return total_ok
