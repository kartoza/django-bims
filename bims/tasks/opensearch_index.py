import logging
from celery import shared_task

logger = logging.getLogger('bims')


@shared_task(name='bims.tasks.index_collection_record', queue='search')
def index_collection_record(record_id: int, schema_name: str):
    from django_tenants.utils import schema_context
    from bims.models.biological_collection_record import BiologicalCollectionRecord
    from bims.opensearch.documents import index_record

    with schema_context(schema_name):
        try:
            record = BiologicalCollectionRecord.objects.select_related(
                'site__river',
                'taxonomy__endemism',
                'taxonomy__iucn_status',
                'taxonomy__origin',
                'module_group',
                'owner',
            ).prefetch_related(
                'taxonomy__tags',
                'taxonomy__vernacular_names',
                'taxonomy__taxongroup_set',
            ).get(id=record_id)
        except BiologicalCollectionRecord.DoesNotExist:
            logger.warning(
                'Record %s not found in schema %s, skipping index',
                record_id, schema_name,
            )
            return

        index_record(record, schema_name=schema_name)
        logger.debug('Indexed record %s/%s', schema_name, record_id)


@shared_task(name='bims.tasks.delete_collection_record_from_index', queue='search')
def delete_collection_record_from_index(record_id: int, schema_name: str):
    from bims.opensearch.documents import delete_record
    delete_record(record_id, schema_name=schema_name)
    logger.debug('Deleted record %s/%s from index', schema_name, record_id)
