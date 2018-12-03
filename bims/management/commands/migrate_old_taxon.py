# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from bims.models import (
    Taxon,
    TaxonIdentifier,
)
from bims.utils.gbif import process_taxon_identifier


class Command(BaseCommand):
    help = 'Migrate old taxon models'

    def handle(self, *args, **options):
        taxa = Taxon.objects.all()
        for taxon in taxa:
            print('Migrate %s' % taxon.scientific_name)
            taxon_identifier = process_taxon_identifier(taxon.gbif_id)
            if taxon_identifier:
                taxon_identifier.iucn_status = taxon.iucn_status
                taxon_identifier.iucn_data = taxon.iucn_data
                taxon_identifier.iucn_redlist_id = taxon.iucn_redlist_id
                taxon_identifier.save()
