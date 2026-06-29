import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger('bims')


class Command(BaseCommand):
    help = (
        'Bulk (re)index all BiologicalCollectionRecords into OpenSearch. '
        'Iterates every non-public tenant schema.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Drop and recreate the index before indexing.',
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=500,
            help='Number of documents per bulk request (default: 500).',
        )
        parser.add_argument(
            '--schema',
            help='Only reindex a single tenant schema (e.g. --schema=tenant1).',
        )

    def handle(self, *args, **options):
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

        recreate = options['recreate']
        chunk_size = options['chunk_size']
        only_schema = options.get('schema')
        with schema_context(get_public_schema_name()):
            run = OpenSearchReindexRun.objects.create(
                status=OpenSearchReindexRun.RUNNING,
                recreate=recreate,
                chunk_size=chunk_size,
                requested_schema=only_schema or '',
            )

        try:
            # Ensure the cluster allows enough buckets for large site_id aggregations.
            get_client().cluster.put_settings(body={
                'persistent': {'search.max_buckets': 200000}
            })
        except Exception as exc:
            self.stderr.write(f'Warning: could not set search.max_buckets: {exc}')

        try:
            create_index(recreate=recreate)

            tenants = get_tenant_model().objects.exclude(schema_name='public')
            if only_schema:
                tenants = tenants.filter(schema_name=only_schema)
            tenants = list(tenants)

            with schema_context(get_public_schema_name()):
                run.total_tenants = len(tenants)
                run.save(update_fields=['total_tenants'])

            tenant_statuses = {}
            with schema_context(get_public_schema_name()):
                for tenant in tenants:
                    tenant_statuses[tenant.schema_name] = (
                        OpenSearchReindexTenantStatus.objects.create(
                            run=run,
                            schema_name=tenant.schema_name,
                        )
                    )

            for tenant in tenants:
                tenant_status = tenant_statuses[tenant.schema_name]
                with schema_context(get_public_schema_name()):
                    tenant_status.status = OpenSearchReindexTenantStatus.RUNNING
                    tenant_status.started_at = timezone.now()
                    tenant_status.error = ''
                    tenant_status.save(
                        update_fields=['status', 'started_at', 'error']
                    )

                self.stdout.write(f'Indexing schema: {tenant.schema_name}')
                try:
                    with tenant_context(tenant):
                        indexed = bulk_index(
                            schema_name=tenant.schema_name,
                            chunk_size=chunk_size,
                        )
                except Exception as exc:
                    with schema_context(get_public_schema_name()):
                        tenant_status.status = OpenSearchReindexTenantStatus.FAILED
                        tenant_status.error = str(exc)
                        tenant_status.finished_at = timezone.now()
                        tenant_status.save(
                            update_fields=['status', 'error', 'finished_at']
                        )
                        run.failed_tenants += 1
                        run.save(update_fields=['failed_tenants'])
                    self.stderr.write(
                        self.style.ERROR(
                            f'  Failed: {tenant.schema_name} - {exc}'
                        )
                    )
                    continue

                with schema_context(get_public_schema_name()):
                    tenant_status.status = OpenSearchReindexTenantStatus.COMPLETED
                    tenant_status.records_indexed = indexed
                    tenant_status.finished_at = timezone.now()
                    tenant_status.save(
                        update_fields=['status', 'records_indexed', 'finished_at']
                    )
                    run.completed_tenants += 1
                    run.save(update_fields=['completed_tenants'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Done: {indexed} records indexed for {tenant.schema_name}'
                    )
                )
        except Exception as exc:
            with schema_context(get_public_schema_name()):
                run.finalize(OpenSearchReindexRun.FAILED, str(exc))
            raise

        with schema_context(get_public_schema_name()):
            if run.failed_tenants > 0:
                run.finalize(
                    OpenSearchReindexRun.FAILED,
                    'One or more tenant reindex operations failed.',
                )
            else:
                run.finalize(OpenSearchReindexRun.COMPLETED)
