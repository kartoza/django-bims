# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import models
from bims.models import (
    Taxon,
    IUCNStatus,
    Taxonomy,
    BiologicalCollectionRecord
)
from bims.models.taxonomy import taxonomy_pre_save_handler
from bims.models.biological_collection_record import (
    collection_post_save_handler,
)
from bims.utils.gbif import process_taxon_identifier


class Command(BaseCommand):
    help = 'Migrate old taxon models'

    def handle(self, *args, **options):
        models.signals.pre_save.disconnect(
            taxonomy_pre_save_handler,
        )
        models.signals.post_save.disconnect(
            collection_post_save_handler,
        )

        taxa = Taxon.objects.all()
        for taxon in taxa:
            print('Migrate %s' % taxon.scientific_name)
            taxon_identifier = process_taxon_identifier(taxon.gbif_id)
            if taxon_identifier:
                taxon_identifier.iucn_data = taxon.iucn_data
                taxon_identifier.iucn_redlist_id = taxon.iucn_redlist_id
                taxon_identifier.author = taxon.author
                taxon_identifier.save()
                if taxon.iucn_status:
                    iucn_status = IUCNStatus.objects.get(
                        pk=taxon.iucn_status.pk)
                    taxonomy = Taxonomy.objects.get(id=taxon_identifier.id)
                    taxonomy.iucn_status = iucn_status
                    taxonomy.save()

        collections = BiologicalCollectionRecord.objects.filter(
            taxonomy__isnull=True,
            taxon_gbif_id__isnull=False
        )
        for collection in collections:
            print('Move taxonomy value for %s - %s' % (
            collection.original_species_name, collection.pk))
            if not collection.taxon_gbif_id:
                continue

            if not collection.taxon_gbif_id.gbif_id:
                continue

            if collection.pk == 20244:
                print('something')

            taxonomy = Taxonomy.objects.get(
                gbif_key=collection.taxon_gbif_id.gbif_id
            )
            collection.taxonomy = taxonomy
            collection.taxon_gbif_id = None
            collection.save()
