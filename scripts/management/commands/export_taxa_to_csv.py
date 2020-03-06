# -*- coding: utf-8 -*-
import logging
import os
import csv
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.conf import settings
from bims.models import Taxonomy, TaxonGroup

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-g',
            '--taxon-group',
            dest='taxon_group',
            default='Algae',
            help='Taxon Group'
        )
        parser.add_argument(
            '-i',
            '--identifier',
            dest='identifier',
            default='',
            help='Identifier for filters'
        )

    def handle(self, *args, **options):
        taxon_group = options.get('taxon_group')
        identifier = options.get('identifier')

        filters = dict()
        taxonomies = []
        taxon_groups = TaxonGroup.objects.filter(
            name__iexact=taxon_group,
            category='SPECIES_MODULE'
        )
        for group in taxon_groups:
            taxonomies.extend(
                list(group.taxonomies.values_list('id', flat=True)))

        or_condition = Q()
        group_filters = [
            'id__in',
            'parent__id__in',
            'parent__parent__id__in',
            'parent__parent__parent__id__in',
            'parent__parent__parent__parent__id__in',
        ]
        for group_filter in group_filters:
            or_condition |= Q(**{
                group_filter: taxonomies})

        taxa = Taxonomy.objects.filter(or_condition)
        if identifier:
            identifiers = identifier.split('=')
            filters[identifiers[0]] = identifiers[1]
            taxa = taxa.filter(additional_data__contains=filters)

        csv_path = os.path.join(settings.MEDIA_ROOT, 'taxa_csv')
        if not os.path.exists(csv_path) : os.mkdir(csv_path)
        csv_file_path = os.path.join(csv_path, '{t}.csv'.format(
            t=taxon_group
        ))

        with open(csv_file_path, mode='w') as csv_file:
            writer = csv.writer(
                csv_file, delimiter=',', quotechar='"',
                quoting=csv.QUOTE_MINIMAL)
            writer.writerow([
                'Rank', 'Taxon', 'Scientific name & Authority', 'GBIF url'])
            for taxon in taxa:
                writer.writerow([
                    taxon.rank,
                    taxon.canonical_name,
                    taxon.scientific_name.encode('utf-8'),
                    'https://gbif.org/species/{}'.format(taxon.gbif_key) if
                    taxon.gbif_key else '-'
                ])
