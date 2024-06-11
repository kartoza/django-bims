import logging

from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import F, CharField, Count
from django.db.models.functions import Concat

from bims.models import TaxonGroup
from bims.models.location_site import LocationSite
from bims.models.survey import Survey


logger = logging.getLogger('bims')


class Command(BaseCommand):
    """
    Validate taxon
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--simulate',
            dest='simulate',
            default=None,
        )
        parser.add_argument(
            '-tg',
            '--taxon_group',
            dest='taxon_group',
            default=None,
        )

    def validate_taxon(self, simulate, taxon_group: TaxonGroup):
        taxa = taxon_group.taxonomies.all()
        logger.debug(f'Found {taxa.count()} sites to validate')
        if not simulate:
            for taxon in taxa:
                logger.debug(f'Validating {taxon.canonical_name}')
                try:
                    TaxonGroupTaxonomy.objects.update_or_create(
                        taxongroup=taxon_group,
                        taxonomy=taxon,
                        defaults={
                            'is_validated': True
                        }
                    )
                except Exception as e:
                    logger.debug(f'Error validating {taxon.canonical_name}: {e}')

        else:
            logger.debug(f'Simulation: Would validate {taxa.count()} taxa')

    def handle(self, *args, **options):
        simulate = options.get('simulate', 'True') == 'True'
        taxon_groups = TaxonGroup.objects.filter(
            id__in=options.get('taxon_group', '').split(',')
        )
        for taxon_group in taxon_groups:
            logger.debug(f'Validating taxon group {taxon_group.name}')
            self.validate_taxon(simulate, taxon_group)
