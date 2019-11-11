# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from bims.models import BiologicalCollectionRecord, Taxonomy
from bims.utils.logger import log
from bims.utils.gbif import find_species


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--taxon_name',
            dest='taxon_name',
            default=None,
            help='Taxon name'
        )

    def handle(self, *args, **options):
        taxon_name = options.get('taxon_name', None)
        if not taxon_name:
            log('Missing taxon name')
            return
        taxa = Taxonomy.objects.filter(
            scientific_name=taxon_name
        )
        if not taxa:
            log('Taxa not found')
            return
        if taxa.count() == 1:
            log('No duplication found')
            return
        log('Taxa found : %s' % taxa.count())

        gbif_key_found = False
        taxa_sample_index = 0
        gbif_key = None
        while not gbif_key_found and taxa_sample_index < taxa.count():
            taxa_sample = taxa[taxa_sample_index]
            rank = taxa_sample.rank
            gbif_response = find_species(
                taxa_sample.scientific_name, rank=rank)
            if 'nubKey' in gbif_response:
                gbif_key_found = True
                gbif_key = gbif_response['nubKey']
            else:
                taxa_sample_index += 1
        if not gbif_key:
            log('Gbif key not found')
            return

        # Find taxon with gbif key
        taxon_with_gbif_key = taxa.filter(gbif_key=gbif_key)
        if not taxon_with_gbif_key:
            log('Taxon with gbif key not found')
            return
        taxon_with_gbif_key = taxon_with_gbif_key[0]
        taxa_without_gbif_key = taxa.exclude(gbif_key=gbif_key)

        for taxon in taxa_without_gbif_key:
            children_taxa = Taxonomy.objects.filter(parent=taxon)
            children_taxa.update(parent=taxon_with_gbif_key)
            bio = BiologicalCollectionRecord.objects.filter(taxonomy=taxon)
            bio.update(taxonomy=taxon_with_gbif_key)

        taxa_without_gbif_key.delete()
