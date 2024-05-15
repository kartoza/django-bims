import logging

from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import F, CharField, Count
from django.db.models.functions import Concat

from bims.models.location_site import LocationSite
from bims.models.survey import Survey


logger = logging.getLogger('bims')


class Command(BaseCommand):
    """
    Combine duplicated surveys
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--simulate',
            dest='simulate',
            default=None,
        )

    def delete_in_batches(self, queryset, batch_size=100):
        with transaction.atomic():
            while queryset.exists():
                # Delete a batch of records
                ids = queryset.values_list('id', flat=True)[:batch_size]
                queryset.filter(id__in=list(ids)).delete()
                logger.debug(f'Deleted batch of {batch_size} sites')

    def delete_legacy_site(self, simulate):
        sites = LocationSite.objects.filter(
            biological_collection_record__isnull=True,
            chemical_collection_record__isnull=True,
            watertemperature__isnull=True
        ).exclude(map_reference='Wetland layer')
        logger.debug(f'Found {sites.count()} sites to delete')
        if not simulate:
            self.delete_in_batches(sites)
        else:
            logger.debug(f'Simulation: Would delete {sites.count()} sites')

    def handle(self, *args, **options):
        simulate = options.get('simulate', None)
        self.delete_legacy_site(simulate)
