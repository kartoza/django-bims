# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import models
from bims.models import (
    Taxon,
    Taxonomy,
)
from bims.models.taxonomy import taxonomy_pre_save_handler
from bims.enums.taxonomic_rank import TaxonomicRank


class Command(BaseCommand):
    help = 'Migrate endemism'

    def handle(self, *args, **options):
        models.signals.pre_save.disconnect(
            taxonomy_pre_save_handler,
        )

        taxonomies = Taxonomy.objects.filter(
            rank=TaxonomicRank.SPECIES.name
        )

        for taxonomy in taxonomies:
            taxon = Taxon.objects.filter(gbif_id=taxonomy.gbif_key)
            if taxon:
                taxonomy.endemism = taxon[0].endemism
                taxonomy.save()

        models.signals.pre_save.connect(
            taxonomy_pre_save_handler,
        )
