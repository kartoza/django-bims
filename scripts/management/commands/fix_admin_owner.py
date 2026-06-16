import csv
import sys

from django.core.management import BaseCommand

from bims.models.biological_collection_record import BiologicalCollectionRecord

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None


class Command(BaseCommand):
    help = (
        'Find biological collection records where owner is an admin/superuser '
        'but collector_user is not. Use --fix to set owner = collector_user '
        'on those records.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Report affected records without making any changes.',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            dest='fix',
            help='Set owner = collector_user on affected records.',
        )
        parser.add_argument(
            '--tenant',
            metavar='SCHEMA',
            help='Target schema name when using django-tenants. If omitted, runs in current schema.',
        )
        parser.add_argument(
            '--output',
            metavar='FILE',
            default='admin_owner_records.csv',
            help='CSV file path for dry-run export (default: admin_owner_records.csv).',
        )
        parser.add_argument(
            '--exclude-admin',
            metavar='USERNAME',
            nargs='+',
            dest='exclude_admins',
            default=[],
            help='Superuser usernames to exclude from the admin-owner check (e.g. kate_snaddon).',
        )

    def handle(self, *args, **options):
        schema = options.get('tenant')

        if schema:
            if schema_context is None:
                self.stderr.write(
                    self.style.ERROR('This command requires django-tenants but it is not available.')
                )
                sys.exit(1)

            tenant = self._get_tenant(schema)
            if not tenant:
                sys.exit(1)

            with schema_context(tenant.schema_name):
                self.stdout.write(self.style.HTTP_INFO(f'Running in tenant schema: {schema}'))
                self._run(options, label=f"tenant '{schema}'")
        else:
            self.stdout.write(self.style.HTTP_INFO('Running in current schema'))
            self._run(options, label='current schema')

    def _run(self, options, label):
        dry_run = options['dry_run']
        fix = options['fix']

        exclude_admins = options['exclude_admins']

        # Records where owner is an admin but collector_user is a non-admin
        records = BiologicalCollectionRecord.objects.filter(
            owner__is_superuser=True,
            collector_user__isnull=False,
            collector_user__is_superuser=False,
        )
        if exclude_admins:
            records = records.exclude(owner__username__in=exclude_admins)
            self.stdout.write(f'[{label}] Excluding admin usernames: {", ".join(exclude_admins)}')
        records = records.select_related('collector_user', 'owner')

        total = BiologicalCollectionRecord.objects.count()
        self.stdout.write(f'[{label}] Total collection records : {total}')
        self.stdout.write(f'[{label}] Records with admin owner + non-admin collector_user: {records.count()}')

        if not records.exists():
            self.stdout.write(self.style.SUCCESS(f'[{label}] No affected records found.'))
            return

        if dry_run:
            csv_path = options['output']
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'id',
                    'owner_id', 'owner',
                    'collector_user_id', 'collector_user',
                    'proposed_owner',
                ])
                for record in records.iterator():
                    owner_name = record.owner.get_full_name() or record.owner.username
                    collector_name = record.collector_user.get_full_name() or record.collector_user.username
                    writer.writerow([
                        record.id,
                        record.owner_id, owner_name,
                        record.collector_user_id, collector_name,
                        collector_name,
                    ])
            self.stdout.write(
                self.style.WARNING(
                    f'\n[{label}] Dry run - no changes made. '
                    f'Affected records exported to {csv_path}. '
                    'Re-run with --fix to apply corrections.'
                )
            )
            return

        if not fix:
            self.stdout.write(
                self.style.WARNING(f'\n[{label}] Pass --fix to apply corrections.')
            )
            return

        updated = 0
        for record in records.iterator():
            old_owner = record.owner.get_full_name() or record.owner.username
            new_owner = record.collector_user.get_full_name() or record.collector_user.username
            record.owner = record.collector_user
            record.save(update_fields=['owner'])
            updated += 1
            self.stdout.write(
                f'[{label}] Record {record.id}: owner {old_owner} -> {new_owner}'
            )

        self.stdout.write(self.style.SUCCESS(f'[{label}] Updated {updated} records.'))

    def _get_tenant(self, schema_name):
        Tenant = get_tenant_model()
        try:
            return Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Tenant with schema '{schema_name}' not found.")
            )
            return None
