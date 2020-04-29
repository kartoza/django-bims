# -*- coding: utf-8 -*-
import logging
from django.core.management.base import BaseCommand
from geonode.people.models import Profile
from bims.models.taxon_group import TaxonGroup
from bims.models.taxonomy import Taxonomy
from bims.scripts.import_gbif_occurrences import import_gbif_occurrences

logger = logging.getLogger('bims')


class Command(BaseCommand):
    help = 'Fetch occurrences from gbif'

    def add_arguments(self, parser):
        parser.add_argument(
            '-g',
            '--taxon-group',
            dest='taxon_group',
            default='Fish',
            help='Taxon group name')
        parser.add_argument(
            '-e',
            '--collector-email',
            dest='collector_email',
            default=None,
            help='Collector email')

    def handle(self, *args, **options):
        taxon_group = TaxonGroup.objects.filter(
            name=options.get('taxon_group')
        )
        if not taxon_group.exists():
            print('Taxon group does not exists')
            return

        taxa = Taxonomy.objects.filter(
            id__in=taxon_group.values('taxonomies'),
            rank='SPECIES'
        ).exclude(gbif_key__isnull=True)

        logger.info('Harvest occurrences from taxon group'
                    ' - {group} - with total species {total} : '.format(
                        group=options.get('taxon_group'),
                        total=taxa.count()
                    ))

        owners = Profile.objects.filter(
            email=options.get('collector_email')
        )
        owner = None
        if owners.exists():
            owner = owners[0]

        for taxon in taxa:
            logger.info('- Species : {}'.format(taxon.canonical_name))
            import_gbif_occurrences(
                taxonomy=taxon,
                owner=owner
            )
