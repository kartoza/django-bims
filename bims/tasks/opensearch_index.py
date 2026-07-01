import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('bims')


@shared_task(name='bims.tasks.opensearch_reindex', queue='search')
def opensearch_reindex(run_id: int):
    from django_tenants.utils import (
        get_public_schema_name,
        get_tenant_model,
        schema_context,
        tenant_context,
    )
    from bims.opensearch.indices import create_index
    from bims.opensearch.documents import bulk_index
    from bims.opensearch.client import get_client
    from bims.models.opensearch_reindex import (
        OpenSearchReindexRun,
        OpenSearchReindexTenantStatus,
    )

    public = get_public_schema_name()

    with schema_context(public):
        try:
            run = OpenSearchReindexRun.objects.get(pk=run_id)
        except OpenSearchReindexRun.DoesNotExist:
            logger.error('OpenSearchReindexRun %s not found', run_id)
            return

        run.status = OpenSearchReindexRun.RUNNING
        run.save(update_fields=['status'])
        recreate = run.recreate
        chunk_size = run.chunk_size
        only_schema = run.requested_schema or None

    try:
        try:
            get_client().cluster.put_settings(body={
                'persistent': {'search.max_buckets': 200000}
            })
        except Exception as exc:
            logger.warning('Could not set search.max_buckets: %s', exc)

        create_index(recreate=recreate)

        tenants = get_tenant_model().objects.exclude(schema_name='public')
        if only_schema:
            tenants = tenants.filter(schema_name=only_schema)
        tenants = list(tenants)

        with schema_context(public):
            run.total_tenants = len(tenants)
            run.save(update_fields=['total_tenants'])

        tenant_statuses = {}
        with schema_context(public):
            for tenant in tenants:
                tenant_statuses[tenant.schema_name] = (
                    OpenSearchReindexTenantStatus.objects.create(
                        run=run,
                        schema_name=tenant.schema_name,
                    )
                )

        for tenant in tenants:
            tenant_status = tenant_statuses[tenant.schema_name]
            with schema_context(public):
                tenant_status.status = OpenSearchReindexTenantStatus.RUNNING
                tenant_status.started_at = timezone.now()
                tenant_status.error = ''
                tenant_status.save(update_fields=['status', 'started_at', 'error'])

            logger.info('Indexing schema: %s', tenant.schema_name)
            try:
                def _on_progress(count):
                    with schema_context(public):
                        tenant_status.records_indexed = count
                        tenant_status.save(update_fields=['records_indexed'])

                with tenant_context(tenant):
                    indexed = bulk_index(
                        schema_name=tenant.schema_name,
                        chunk_size=chunk_size,
                        on_progress=_on_progress,
                    )
            except Exception as exc:
                with schema_context(public):
                    tenant_status.status = OpenSearchReindexTenantStatus.FAILED
                    tenant_status.error = str(exc)
                    tenant_status.finished_at = timezone.now()
                    tenant_status.save(
                        update_fields=['status', 'error', 'finished_at']
                    )
                    run.failed_tenants += 1
                    run.save(update_fields=['failed_tenants'])
                logger.error('Failed schema %s: %s', tenant.schema_name, exc)
                continue

            with schema_context(public):
                tenant_status.status = OpenSearchReindexTenantStatus.COMPLETED
                tenant_status.records_indexed = indexed
                tenant_status.finished_at = timezone.now()
                tenant_status.save(
                    update_fields=['status', 'records_indexed', 'finished_at']
                )
                run.completed_tenants += 1
                run.save(update_fields=['completed_tenants'])
            logger.info('Done: %s records for %s', indexed, tenant.schema_name)

    except Exception as exc:
        with schema_context(public):
            run.finalize(OpenSearchReindexRun.FAILED, str(exc))
        raise

    with schema_context(public):
        if run.failed_tenants > 0:
            run.finalize(
                OpenSearchReindexRun.FAILED,
                'One or more tenant reindex operations failed.',
            )
        else:
            run.finalize(OpenSearchReindexRun.COMPLETED)


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
                'site__locationcontext_set__group',
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
