# -*- coding: utf-8 -*-
import logging
import os
import csv
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.conf import settings
from bims.models import Taxonomy, TaxonGroup, BiologicalCollectionRecord

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    taxon_rank = [
        'KINGDOM',
        'PHYLUM',
        'CLASS',
        'ORDER',
        'FAMILY',
        'GENUS',
        'SPECIES'
    ]

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
        parser.add_argument(
            '-ti',
            '--taxa-identifier',
            dest='taxa_identifier',
            default='',
            help='Identifier for taxa filters'
        )

    def handle(self, *args, **options):
        taxon_group = options.get('taxon_group')
        identifier = options.get('identifier')
        taxa_identifier = options.get('taxa_identifier')
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
        if taxa_identifier:
            taxa_identifiers = taxa_identifier.split('=')
            filters[taxa_identifiers[0]] = taxa_identifiers[1]
            taxa = Taxonomy.objects.filter(additional_data__contains=filters)
        elif identifier:
            identifiers = identifier.split('=')
            filters[identifiers[0]] = identifiers[1]
            bio = BiologicalCollectionRecord.objects.filter(
                additional_data__contains=filters
            )
            taxa = Taxonomy.objects.filter(
                id__in=bio.values('taxonomy')
            )

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
                'Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus',
                'Species', 'Taxon', 'Scientific name & Authority', 'GBIF url'])
            for taxon in taxa:
                data = {}

                current_taxon = taxon
                if current_taxon.rank in self.taxon_rank:
                    data[current_taxon.rank] = taxon.canonical_name
                while current_taxon.parent:
                    current_taxon = current_taxon.parent
                    if current_taxon.rank in self.taxon_rank:
                        data[current_taxon.rank] = (
                            current_taxon.canonical_name.encode('utf-8')
                        )

                # sort by rank
                csv_data = []
                for rank in self.taxon_rank:
                    csv_data.append(data[rank] if rank in data else '-')

                csv_data.append(taxon.canonical_name.encode('utf-8'))
                csv_data.append(taxon.scientific_name.encode('utf-8'))
                csv_data.append('https://gbif.org/species/{}'.format(
                    taxon.gbif_key) if
                    taxon.gbif_key else '-')

                writer.writerow(csv_data)
