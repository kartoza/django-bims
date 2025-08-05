# coding=utf-8
"""Add group to location context document."""
import ast
import sys
try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None
from django.core.management.base import BaseCommand
from django.db.models import signals
from bims.utils.location_context import get_location_context_data
from bims.models.location_context_group import (
    LocationContextGroup
)


class Command(BaseCommand):
    """Add group to location context document
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--only-empty',
            dest='only_empty',
            default=False,
            help='Only update empty location context')

        parser.add_argument(
            '-g',
            '--groups',
            dest='groups',
            default=None,
            help='Geocontext groups keys')

        parser.add_argument(
            '-s',
            '--site-id',
            dest='site_id',
            default=None,
            help='Update location context for specific site')

        parser.add_argument(
            '-sc',
            '--site-code',
            dest='site_code',
            default='False',
            help='Generate site code')

        parser.add_argument(
            '--tenant',
            dest='tenant',
            default=None,
            help='Tenant schema name'
        )

    def handle(self, *args, **options):
        schema = options.get('tenant')

        if schema:
            if schema_context is None:
                self.stderr.write("This command requires django-tenants but it is not available.")
                sys.exit(1)

            tenant = self._get_tenant(schema)
            if not tenant:
                sys.exit(1)

            with schema_context(tenant.schema_name):
                self.stdout.write(f"Running in tenant schema: {schema}")
                self._run_update(options)
        else:
            self.stdout.write("Running in current schema")
            self._run_update(options)
        return

    def _run_update(self, options):
        from bims.models.location_context_filter_group_order import (
            location_context_post_save_handler
        )

        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextGroup
        )

        generate_site_code = ast.literal_eval(
            options.get('site_code')
        )

        get_location_context_data(
            group_keys=options.get('groups', None),
            site_id=options.get('site_id', None),
            only_empty=options.get('only_empty', False),
            should_generate_site_code=generate_site_code
        )

    def _get_tenant(self, schema_name):
        Tenant = get_tenant_model()
        try:
            return Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            self.stderr.write(f"Tenant with schema '{schema_name}' not found.")
            return None
