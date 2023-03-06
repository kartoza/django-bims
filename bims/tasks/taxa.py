# coding=utf-8
import csv

from celery import shared_task
from bims.scripts.species_keys import *  # noqa


@shared_task(name='bims.tasks.fetch_vernacular_names', queue='update')
def fetch_vernacular_names(taxa_ids: []):
    from bims.models.taxonomy import Taxonomy
    from bims.utils.fetch_gbif import fetch_gbif_vernacular_names

    taxa = Taxonomy.objects.filter(
        id__in=[str(taxa_id) for taxa_id in taxa_ids]
    )
    for taxon in taxa:
        fetch_gbif_vernacular_names(taxon)
