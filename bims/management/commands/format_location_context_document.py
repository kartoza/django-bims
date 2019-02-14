from django.core.management.base import BaseCommand
from bims.utils.location_context import format_location_context
from bims.models.location_site import LocationSite


class Command(BaseCommand):
    """Format location context document.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--location-site-id',
            dest='site_id',
            default=False,
            help='Format location context document for site id')

        parser.add_argument(
            '-f',
            '--force-update',
            dest='force_update',
            default=False,
            help='Ignore cache')

    def handle(self, *args, **options):
        site_id = options.get('site_id', None)
        force_update = options.get('force_update', False)
        if site_id:
            format_location_context(site_id, force_update)
        else:
            sites = LocationSite.objects.filter(
                location_context_document__isnull=False
            )
            index = 1
            for site in sites:
                print('site %s of %s' % (index, len(sites)))
                format_location_context(site.id)
                index += 1
        return
