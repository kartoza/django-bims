import json
from django.core.management.base import BaseCommand
from django.contrib.gis.db import models
from bims.utils.iucn import get_iucn_status
from bims.models.taxonomy import Taxonomy
from bims.models.biological_collection_record import (
    collection_post_save_update_cluster,
    collection_post_save_handler
)
from bims.models.iucn_status import IUCNStatus


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
            print('Update taxon : %s' % taxon.common_name)
            if taxon.species:
                iucn_status = get_iucn_status(
                        species_name=taxon.species,
                        only_returns_json=True
                )
            else:
                iucn_status = get_iucn_status(
                        species_name=taxon.common_name,
                        only_returns_json=True
                )
            if not iucn_status:
                # let's try fetch with gbif id
                iucn_status = get_iucn_status(taxon_id=taxon.gbif_id,
                                              only_returns_json=True)

            if 'result' in iucn_status:
                iucn, status = IUCNStatus.objects.get_or_create(
                        category=iucn_status['result'][0]['category']
                )
                taxon.iucn_status = iucn
                taxon.iucn_redlist_id = iucn_status['result'][0]['taxonid']
                taxon.iucn_data = json.dumps(
                        iucn_status['result'][0],
                        indent=4)
                taxon.save()

            print(iucn_status)

        models.signals.post_save.connect(
                collection_post_save_update_cluster,
        )
        models.signals.post_save.connect(
                collection_post_save_handler,
        )
