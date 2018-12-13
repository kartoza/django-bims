# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from bims.models import (
    TaxonGroup,
    Taxonomy
)
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


class Command(BaseCommand):

    def handle(self, *args, **options):
        taxonomies = Taxonomy.objects.filter(
            rank=TaxonomicRank.SPECIES.name
        )
        for taxonomy in taxonomies:
            taxonomy_classname = taxonomy.class_name
            if taxonomy_classname:
                taxon_group, status = TaxonGroup.objects.get_or_create(
                    name=taxonomy_classname,
                    category=TaxonomicGroupCategory.SPECIES_CLASS.name
                )
                print('Updating taxon group %s' % taxon_group.name)
                taxon_group.taxonomies.add(taxonomy)
                taxon_group.save()
