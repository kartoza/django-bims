# -*- coding: utf-8 -*-
"""
Management command: harvest_iucn_africa_taxa

Queries the IUCN Red List API v4 for taxon groups and prints a summary
(or writes JSON output to a file).  Supports multi-tenant deployments.

Taxon groups covered
--------------------
Freshwater fish  – Actinopterygii + Chondrichthyes
Amphibia         – Amphibia
Mollusca         – Mollusca (phylum)
Crustacea        – Malacostraca + Maxillopoda + Branchiopoda + Ostracoda
Odonata          – Odonata (order)

Filters applied for every group
--------------------------------
Land regions : North Africa (code 14) + Sub-Saharan Africa (code 11)
Habitat      : 5 – Wetlands (inland)
Include      : species + subspecies/varieties
"""
import json
import logging
import sys

from django.core.management.base import BaseCommand, CommandError

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None

from bims.utils.iucn import IUCN_TAXON_GROUPS, harvest_iucn_taxa

logger = logging.getLogger('bims')


class Command(BaseCommand):
    help = (
        'Harvest IUCN Red List taxa '
        '(freshwater fish, amphibia, mollusca, crustacea, odonata) '
        'filtered to African land regions and inland wetland habitat. '
        'Supports multi-tenant deployments via --tenant / --all-tenants.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-g', '--groups',
            dest='groups',
            default=None,
            help=(
                'Comma-separated list of group names to harvest. '
                'Choices: {}. '
                'Defaults to all groups.'.format(
                    ', '.join(IUCN_TAXON_GROUPS.keys())
                )
            ),
        )
        parser.add_argument(
            '-o', '--output',
            dest='output',
            default=None,
            help='Optional path to write JSON results to (e.g. /tmp/iucn.json).',
        )
        parser.add_argument(
            '--habitat',
            dest='habitat_name',
            default='wetland',
            help='Habitat name substring to filter by (default: "wetland").',
        )
        parser.add_argument(
            '--max-pages',
            dest='max_pages',
            type=int,
            default=None,
            help='Stop after this many pages per taxonomy lookup (for testing).',
        )
        parser.add_argument(
            '--all-assessments',
            dest='all_assessments',
            action='store_true',
            default=False,
            help='Fetch all assessments, not just the latest per taxon.',
        )
        parser.add_argument(
            '--delay',
            dest='delay',
            type=float,
            default=1.0,
            help='Seconds to sleep between API requests (default: 1.0).',
        )
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
            help='Iterate through every tenant schema (excludes public).',
        )

    def handle(self, *args, **options):
        tenant_schema = options.get('tenant')
        all_tenants = options.get('all_tenants')

        if tenant_schema and all_tenants:
            raise CommandError("Use either --tenant or --all-tenants, not both.")

        group_names = self._parse_groups(options)
        if group_names is None and options['groups']:
            return  # validation failed inside _parse_groups

        if tenant_schema:
            self._run_in_schema(tenant_schema, group_names, options)
            return

        if all_tenants:
            if get_tenant_model is None or schema_context is None:
                raise CommandError("django-tenants is required for --all-tenants.")
            TenantModel = get_tenant_model()
            tenants = TenantModel.objects.exclude(schema_name='public')
            if not tenants.exists():
                self.stdout.write(self.style.WARNING('No tenant schemas found.'))
                return
            for tenant in tenants:
                self.stdout.write(
                    self.style.MIGRATE_HEADING(f'\nTenant: {tenant.schema_name}')
                )
                with schema_context(tenant.schema_name):
                    self._harvest(group_names, options)
            return

        # Default: run in the current schema
        self._harvest(group_names, options)

    def _parse_groups(self, options):
        raw = options.get('groups')
        if not raw:
            return None
        group_names = [g.strip() for g in raw.split(',')]
        unknown = [g for g in group_names if g not in IUCN_TAXON_GROUPS]
        if unknown:
            self.stderr.write(self.style.ERROR(
                f"Unknown group(s): {unknown}. "
                f"Valid choices: {list(IUCN_TAXON_GROUPS.keys())}"
            ))
            return None
        return group_names

    def _run_in_schema(self, schema_name, group_names, options):
        if get_tenant_model is None or schema_context is None:
            self.stderr.write("django-tenants is required for --tenant.")
            sys.exit(1)
        TenantModel = get_tenant_model()
        try:
            TenantModel.objects.get(schema_name=schema_name)
        except TenantModel.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f"Tenant with schema '{schema_name}' not found."
            ))
            sys.exit(1)
        self.stdout.write(self.style.MIGRATE_HEADING(f'Tenant: {schema_name}'))
        with schema_context(schema_name):
            self._harvest(group_names, options)

    def _harvest(self, group_names, options):
        self.stdout.write(
            'Harvesting: ' + (', '.join(group_names) if group_names else 'ALL groups')
        )

        results = harvest_iucn_taxa(
            group_names=group_names,
            habitat_name=options['habitat_name'],
            latest=not options['all_assessments'],
            request_delay=options['delay'],
            max_pages=options['max_pages'],
        )

        if not results:
            self.stderr.write(self.style.WARNING(
                'No results returned. Check that the IUCN API key is configured '
                'in SiteSetting and that the API is reachable.'
            ))
            return

        self.stdout.write('\nSummary (sis_taxon_ids matching taxonomy + wetland habitat)')
        self.stdout.write('-' * 60)
        total = 0
        for group, sis_ids in results.items():
            self.stdout.write(f'  {group}: {len(sis_ids)} taxa')
            total += len(sis_ids)
        self.stdout.write(f'  TOTAL : {total} taxa')

        if options['output']:
            output_path = options['output']
            try:
                with open(output_path, 'w', encoding='utf-8') as fh:
                    json.dump(results, fh, ensure_ascii=False, indent=2)
                self.stdout.write(self.style.SUCCESS(f'\nResults written to {output_path}'))
            except OSError as exc:
                self.stderr.write(self.style.ERROR(f'Failed to write output: {exc}'))
        else:
            self.stdout.write('\nTip: pass -o /path/to/output.json to save the full results.')
