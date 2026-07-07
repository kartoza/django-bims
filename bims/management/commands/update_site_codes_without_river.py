# coding=utf-8
"""Update site codes for FBIS sites that don't have a river."""
import logging
import sys
try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None
from django.core.management.base import BaseCommand
from django.db.models import Q
from bims.models.location_site import LocationSite, generate_site_code
from bims.signals.utils import disconnect_bims_signals, connect_bims_signals

logger = logging.getLogger('bims')

INVALID_RIVER_CODES = ['LARG', 'MODE', 'SERI', 'TRIB', 'UNMO']


class Command(BaseCommand):
    """Update site codes for FBIS sites without a river."""

    help = 'Update site codes for FBIS sites that have no river assigned'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            dest='tenant',
            default=None,
            help='Tenant schema name (e.g. fbis)'
        )

    def handle(self, *args, **options):
        schema = options.get('tenant')

        if schema:
            if schema_context is None:
                self.stderr.write(
                    'This command requires django-tenants but it is not available.'
                )
                sys.exit(1)
            try:
                Tenant = get_tenant_model()
                tenant = Tenant.objects.get(schema_name=schema)
            except Tenant.DoesNotExist:
                self.stderr.write(f"Tenant with schema '{schema}' not found.")
                sys.exit(1)
            with schema_context(tenant.schema_name):
                logger.info(f'Running in tenant schema: {schema}')
                self._run(options)
        else:
            self._run(options)

    def _run(self, options):
        from preferences import preferences
        site_code_generator = preferences.SiteSetting.site_code_generator
        if site_code_generator != 'fbis':
            logger.error(
                f'This command is only for FBIS. '
                f'Current generator is: {site_code_generator}'
            )
            return

        invalid_code_q = Q()
        for code in INVALID_RIVER_CODES:
            invalid_code_q |= Q(site_code__icontains=code)

        sites = LocationSite.objects.filter(
            Q(river__isnull=True) & invalid_code_q
        ).exclude(
            ecosystem_type__iexact='wetland'
        ).exclude(
            ecosystem_type__iexact='open waterbody'
        )

        total = sites.count()
        logger.info(
            f'Found {total} FBIS sites without a river or with invalid '
            f'river codes {INVALID_RIVER_CODES}'
        )

        disconnect_bims_signals()

        updated = 0
        failed = 0

        for index, site in enumerate(sites.iterator(), 1):
            logger.info(
                f'[{index}/{total}] Processing site {site.id} '
                f'(current code: {site.site_code!r})'
            )
            try:
                site_code, catchments_data = generate_site_code(
                    location_site=site,
                    lat=site.latitude,
                    lon=site.longitude,
                    ecosystem_type=site.ecosystem_type or '',
                )
                if site_code:
                    site.site_code = site_code
                    if catchments_data:
                        site.additional_data = site.additional_data or {}
                        site.additional_data.update(catchments_data)
                    site.save()
                    logger.info(f'Updated site {site.id} -> {site_code!r}')
                    updated += 1
                else:
                    logger.warning(f'No site code generated for site {site.id}')
                    failed += 1
            except Exception as e:
                logger.error(f'Failed for site {site.id}: {e}')
                failed += 1

        connect_bims_signals()

        logger.info(
            f'Done. Updated: {updated}, Failed/Skipped: {failed}'
        )
