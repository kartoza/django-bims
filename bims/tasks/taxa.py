# coding=utf-8
import time
from celery import shared_task
from celery.utils.log import get_task_logger

from django.db import transaction
from django.db.models import Q

logger = get_task_logger(__name__)


@shared_task(name='bims.tasks.fetch_vernacular_names', queue='update')
def fetch_vernacular_names(taxa_ids: []):
    from bims.models.taxonomy import Taxonomy
    from bims.utils.fetch_gbif import fetch_gbif_vernacular_names

    taxa = Taxonomy.objects.filter(
        id__in=[str(taxa_id) for taxa_id in taxa_ids]
    )
    for taxon in taxa:
        fetch_gbif_vernacular_names(taxon)


@shared_task(name="bims.tasks.fetch_iucn_status", queue="update")
def fetch_iucn_status(taxa_ids: list[int] | None = None, *, batch_size: int = 1000) -> str:
    """
    Harvest (or update) IUCN Red-List information for the requested taxa.
    """
    from bims.models import Taxonomy, IUCNStatus
    from bims.utils.iucn import get_iucn_status

    t0 = time.perf_counter()

    qs = Taxonomy.objects.all()

    if taxa_ids:
        qs = qs.filter(id__in=taxa_ids)

    qs = qs.filter(rank__in=["SPECIES", "SUBSPECIES"])

    total = qs.count()
    logger.info("Starting IUCN sync for %s taxon record(s).", total)

    if not taxa_ids:
        qs = qs.exclude(iucn_data__icontains='url')

    to_update: list[Taxonomy] = []

    for taxon in qs:
        status_obj, sis_id, url = get_iucn_status(taxon=taxon)

        if status_obj is None:
            status_obj, _ = IUCNStatus.objects.get_or_create(
                category="NE",
                national=False
            )

        changed = False
        if taxon.iucn_status_id != status_obj.id:
            taxon.iucn_status = status_obj
            changed = True

        if sis_id and taxon.iucn_redlist_id != sis_id:
            taxon.iucn_redlist_id = sis_id
            changed = True

        if url:
            if not taxon.iucn_data or "url" not in taxon.iucn_data:
                changed = True
            taxon.iucn_data = {"url": url}

        if changed:
            logger.debug(
                "Taxon %s (%s): status → %s, sis_id → %s",
                taxon.id,
                taxon.canonical_name,
                status_obj.category,
                sis_id or "—",
            )
            to_update.append(taxon)

    if to_update:
        with transaction.atomic():
            Taxonomy.objects.bulk_update(
                to_update, [
                    "iucn_status", "iucn_redlist_id", "iucn_data"
                ], batch_size
            )

    dt = time.perf_counter() - t0
    logger.info(
        "IUCN sync finished: %s/%s updated in %.2f s.", len(to_update), total, dt
    )
    return f"Updated {len(to_update)} taxonomy record(s)."
