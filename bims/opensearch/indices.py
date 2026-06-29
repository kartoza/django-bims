import logging
from bims.opensearch.client import get_client

logger = logging.getLogger('bims')

COLLECTIONS_INDEX = 'bims_collections'

COLLECTIONS_MAPPING = {
    'mappings': {
        'properties': {
            # --- tenant isolation ---
            'schema_name': {'type': 'keyword'},

            # --- record identity ---
            'record_id': {'type': 'integer'},
            'uuid': {'type': 'keyword'},

            # --- taxonomy ---
            'taxonomy_id': {'type': 'integer'},
            'canonical_name': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'scientific_name': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'vernacular_names': {'type': 'text'},
            'tags': {'type': 'keyword'},
            'endemism': {'type': 'keyword'},
            'conservation_status': {'type': 'keyword'},
            'origin': {'type': 'keyword'},

            # --- taxon group / module ---
            'module_group_id': {'type': 'integer'},
            'module_group_name': {'type': 'keyword'},
            'taxon_group_ids': {'type': 'integer'},

            # --- site ---
            'site_id': {'type': 'integer'},
            'site_code': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'site_name': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'river_name': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'ecosystem_type': {'type': 'keyword'},
            'location': {'type': 'geo_point'},
            'location_context_groups': {'type': 'keyword'},
            'location_context_values': {'type': 'keyword'},

            # --- collection record ---
            'collection_date': {'type': 'date', 'format': 'yyyy-MM-dd'},
            'collector': {'type': 'text'},
            'original_species_name': {'type': 'text'},
            'data_type': {'type': 'keyword'},

            # --- validation / access control ---
            'owner_id': {'type': 'integer'},
            'is_validated': {'type': 'boolean'},
            'ready_for_validation': {'type': 'boolean'},
            'end_embargo_date': {'type': 'date', 'format': 'yyyy-MM-dd'},
        }
    },
    'settings': {
        'number_of_shards': 1,
        'number_of_replicas': 0,
    },
}


def create_index(recreate=False):
    client = get_client()
    exists = client.indices.exists(index=COLLECTIONS_INDEX)
    if exists:
        if not recreate:
            return
        logger.info('Deleting existing index %s', COLLECTIONS_INDEX)
        client.indices.delete(index=COLLECTIONS_INDEX)
    logger.info('Creating index %s', COLLECTIONS_INDEX)
    client.indices.create(index=COLLECTIONS_INDEX, body=COLLECTIONS_MAPPING)
