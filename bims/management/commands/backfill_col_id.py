# coding=utf-8
"""Backfill missing col_id on Taxonomy records."""

import logging
import sys
import time

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from bims.models.taxonomy import Taxonomy
from bims.utils.col import resolve_col_id

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Backfill col_id on Taxonomy records that are missing it. '
        'Uses gbif_key first (with canonical_name validation), '
        'falling back to canonical_name lookup.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            dest='tenant',
            default=None,
            help='Run against a specific tenant schema name.',
        )
        parser.add_argument(
            '--all-tenants',
            dest='all_tenants',
            action='store_true',
            default=False,
            help='Iterate through every non-public tenant schema.',
        )
        parser.add_argument(
            '--chunk-size',
            dest='chunk_size',
            type=int,
            default=200,
            help='Number of records to iterate per database fetch (default: 200).',
        )
        parser.add_argument(
            '--delay',
            dest='delay',
            type=float,
            default=0.0,
            help='Seconds to sleep between API calls to avoid rate limiting (default: 0).',
        )

    def handle(self, *args, **options):
        tenant = options.get('tenant')
        all_tenants = options.get('all_tenants')

        if tenant and all_tenants:
            raise CommandError('Use either --tenant or --all-tenants, not both.')

        if tenant:
            self._run_for_schema(tenant, options)
            return

        if all_tenants:
            if schema_context is None or get_tenant_model is None:
                raise CommandError(
                    'django-tenants is required for --all-tenants.'
                )
            TenantModel = get_tenant_model()
            tenants = TenantModel.objects.exclude(
                schema_name='public'
            ).order_by('schema_name')
            if not tenants.exists():
                self.stdout.write(self.style.WARNING('No tenant schemas found.'))
                return
            for tenant_obj in tenants:
                self._run_in_schema(tenant_obj.schema_name, options)
            return

        self.stdout.write(self.style.HTTP_INFO('Running in current schema'))
        self._backfill(options)

    def _run_for_schema(self, schema_name, options):
        if schema_context is None or get_tenant_model is None:
            self.stderr.write(
                'This command requires django-tenants but it is not available.'
            )
            sys.exit(1)
        TenantModel = get_tenant_model()
        if not TenantModel.objects.filter(schema_name=schema_name).exists():
            raise CommandError(f'Tenant schema not found: {schema_name}')
        self._run_in_schema(schema_name, options)

    def _run_in_schema(self, schema_name, options):
        with schema_context(schema_name):
            self.stdout.write(
                self.style.HTTP_INFO(f'\n=== Tenant: {schema_name} ===')
            )
            self._backfill(options)

    def _backfill(self, options):
        chunk_size = options.get('chunk_size', 200)
        delay = options.get('delay', 0.0)

        qs = Taxonomy.objects.filter(
            Q(col_id__isnull=True) | Q(col_id='')
        ).filter(
            Q(gbif_key__isnull=False) | ~Q(canonical_name='')
        ).order_by('id')

        total = qs.count()
        if not total:
            self.stdout.write(
                self.style.SUCCESS('No taxa missing col_id. Nothing to do.')
            )
            return

        self.stdout.write(f'Found {total} taxa missing col_id. Starting backfill...\n')

        updated = 0
        skipped = 0
        errors = 0
        processed = 0

        for taxon in qs.iterator(chunk_size=chunk_size):
            processed += 1
            label = (
                f'[{processed}/{total}] id={taxon.id} '
                f'"{taxon.canonical_name}" (gbif_key={taxon.gbif_key})'
            )

            try:
                col_id, _ = resolve_col_id(
                    taxon.gbif_key,
                    taxon.canonical_name or '',
                )
            except Exception as exc:
                self.stderr.write(f'  ERROR {label}: {exc}')
                logger.exception('backfill_col_id: unexpected error for taxon id=%s', taxon.id)
                errors += 1
                continue

            if col_id:
                taxon.col_id = col_id
                taxon.save(update_fields=['col_id'])
                self.stdout.write(
                    self.style.SUCCESS(f'  UPDATED {label} -> col_id={col_id}')
                )
                updated += 1
            else:
                self.stdout.write(f'  SKIPPED {label} (no COL match found)')
                skipped += 1

            if delay:
                time.sleep(delay)

        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Backfill complete. '
                f'total={total}, updated={updated}, skipped={skipped}, errors={errors}'
            )
        )
