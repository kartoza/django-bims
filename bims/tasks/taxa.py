# coding=utf-8
import time
from typing import Iterable

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model

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


def _iter_queryset(qs, *, chunk_size: int = 1000) -> Iterable:
    """
    Memory-safe iterator over a queryset.
    """
    return qs.iterator(chunk_size=chunk_size)


@shared_task(name="bims.tasks.approve_unvalidated_taxa_by_group", queue="update", bind=True)
def approve_unvalidated_taxa_by_group(
    self,
    taxon_group_id: int,
    initiated_by_user_id: int,
    include_children: bool = True,
    chunk_size: int = 500,
) -> str:
    """
    Approve all taxonomy update proposals for a given taxon group.

    Args:
        taxon_group_id: The TaxonGroup to act on.
        initiated_by_user_id: The user performing the approvals (used for auditing).
        include_children: If True, also approve proposals under descendant groups.
        only_status: Limit to proposals in these statuses. Defaults to ["pending"].
        chunk_size: Iterator chunk size for DB reads.

    Returns:
        A short summary string.
    """
    t0 = time.perf_counter()

    from bims.models import TaxonGroup, TaxonGroupTaxonomy, TaxonomyUpdateProposal, Taxonomy
    from bims.api_views.taxon_update import create_taxon_proposal

    User = get_user_model()

    try:
        actor = User.objects.get(pk=initiated_by_user_id)
    except User.DoesNotExist:
        msg = f"Actor user {initiated_by_user_id} does not exist."
        logger.error(msg)
        return msg

    try:
        root_group = TaxonGroup.objects.get(pk=taxon_group_id)
    except TaxonGroup.DoesNotExist:
        msg = f"TaxonGroup {taxon_group_id} does not exist."
        logger.error(msg)
        return msg

    group_ids = [root_group.id]
    if include_children:
        try:
            group_ids.extend([g.id for g in root_group.get_all_children()])
        except Exception as exc:
            logger.exception("Failed to collect descendant groups for %s: %s", root_group.id, exc)

    tgt_qs = (
        TaxonGroupTaxonomy.objects
        .filter(taxongroup_id__in=group_ids,
                is_validated=False,
                is_rejected=False)
        .select_related("taxonomy", "taxongroup")
        .order_by("id")
    )

    total = tgt_qs.count()
    if total == 0:
        msg = f"No unvalidated taxa found for {root_group.name}."
        logger.info(msg)
        return msg

    logger.info(
        "Approving %s proposal(s) for %s (include_children=%s).",
        total, root_group.name, include_children
    )

    created = 0
    approved = 0
    failed = 0
    failed_ids: list[int] = []

    for link in _iter_queryset(tgt_qs, chunk_size=chunk_size):
        taxon: Taxonomy = link.taxonomy
        group: TaxonGroup = link.taxongroup

        proposal = (
            TaxonomyUpdateProposal.objects
            .filter(
                original_taxonomy_id=taxon.id,
                taxon_group_id__in=group_ids,
                status__in=["pending"]
            )
            .order_by("id")
            .first()
        )
        try:
            with transaction.atomic():
                if proposal is None:
                    proposal = create_taxon_proposal(
                        taxon=taxon,
                        taxon_group=group,
                        data={})
                    created += 1

                proposal.approve(actor)

                proposal.refresh_from_db()
                if proposal.status in (None, "", "pending", "created"):
                    proposal.status = "approved"
                    proposal.save(update_fields=["status"])

                if not link.is_validated:
                    link.is_validated = True
                    link.save(update_fields=["is_validated"])

                approved += 1

        except Exception as exc:
            failed += 1
            failed_ids.append(link.id)
            logger.exception(
                "Failed on TaxonGroupTaxonomy id=%s (taxon=%s, group=%s): %s",
                link.id, taxon.id, group.id, exc
            )

        if approved and (approved + failed) % 500 == 0:
            self.update_state(
                state="PROGRESS",
                meta={"processed": approved + failed, "approved": approved, "failed": failed, "total": total},
            )

    dt = time.perf_counter() - t0
    summary = (
        f"Unvalidated taxa processed for {root_group.name}: "
        f"approved={approved}, failed={failed}, total={total} in {dt:.2f}s."
    )
    if failed_ids:
        logger.warning(
            "Proposals failed to approve: %s", failed_ids[:50] + (["…"] if len(failed_ids) > 50 else []))

    logger.info(summary)
    return summary
