import logging
from django.core.management.base import BaseCommand

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
        from django_tenants.utils import get_tenant_model, tenant_context
        from bims.opensearch.indices import create_index
        from bims.opensearch.documents import bulk_index
        from bims.opensearch.client import get_client

        recreate = options['recreate']
        chunk_size = options['chunk_size']
        only_schema = options.get('schema')

        # Ensure the cluster allows enough buckets for large site_id aggregations.
        try:
            get_client().cluster.put_settings(body={
                'persistent': {'search.max_buckets': 200000}
            })
        except Exception as exc:
            self.stderr.write(f'Warning: could not set search.max_buckets: {exc}')

        create_index(recreate=recreate)

        tenants = get_tenant_model().objects.exclude(schema_name='public')
        if only_schema:
            tenants = tenants.filter(schema_name=only_schema)

        for tenant in tenants:
            self.stdout.write(f'Indexing schema: {tenant.schema_name}')
            with tenant_context(tenant):
                indexed = bulk_index(schema_name=tenant.schema_name, chunk_size=chunk_size)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Done: {indexed} records indexed for {tenant.schema_name}'
                    )
                )
