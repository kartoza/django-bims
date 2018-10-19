from django.core.management.base import BaseCommand
from django.contrib.gis.db import models
from bims.utils.iucn import get_iucn_status
from bims.utils.gbif import update_taxonomy_fields, get_species
from bims.models.taxon import Taxon
from bims.models.biological_collection_record import (
    collection_post_save_update_cluster,
    collection_post_save_handler
)


class Command(BaseCommand):
    """Update taxa.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-t',
            '--taxon-id',
            dest='taxon_id',
            default=False,
            help='Update for specific taxon id')

    def handle(self, *args, **options):
        # Get collection without taxa record
        taxon_id = options.get('taxon_id')
        if taxon_id:
            taxons = Taxon.objects.filter(
                pk=taxon_id
            )
        else:
            taxons = Taxon.objects.all()

        models.signals.post_save.disconnect(
                collection_post_save_update_cluster,
        )
        models.signals.post_save.disconnect(
                collection_post_save_handler,
        )
        for taxon in taxons:
            print('Update taxon : %s' % taxon.common_name)
            gbif_result = {}
            if taxon.gbif_id:
                gbif_result = get_species(taxon.gbif_id)
            if gbif_result:
                update_taxonomy_fields(taxon, gbif_result)

        models.signals.post_save.connect(
                collection_post_save_update_cluster,
        )
        models.signals.post_save.connect(
                collection_post_save_handler,
        )
