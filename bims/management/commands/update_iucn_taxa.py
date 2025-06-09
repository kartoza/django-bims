import json
from django.core.management.base import BaseCommand
from django.contrib.gis.db import models
from bims.utils.iucn import get_iucn_statusget_iucn_status, get_iucn_status
from bims.models.taxonomy import Taxonomy
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
            taxa = Taxonomy.objects.filter(
                pk=taxon_id
            )
        else:
            taxa = Taxonomy.objects.all()

        models.signals.post_save.disconnect(
                collection_post_save_update_cluster,
        )
        models.signals.post_save.disconnect(
                collection_post_save_handler,
        )
        for taxon in taxa:
            print('Updating taxon : %s' % taxon.common_name)
            if taxon.is_species:
                iucn_status, sis_id, iucn_url = get_iucn_status(
                    taxon=taxon,
                )

                if iucn_status:
                    taxon.iucn_status = iucn_status

                if sis_id:
                    taxon.iucn_redlist_id = sis_id

                if iucn_url:
                    taxon.iucn_data = {
                        'url': iucn_url
                    }

                if iucn_status or sis_id:
                    taxon.save()

        models.signals.post_save.connect(
                collection_post_save_update_cluster,
        )
        models.signals.post_save.connect(
                collection_post_save_handler,
        )
