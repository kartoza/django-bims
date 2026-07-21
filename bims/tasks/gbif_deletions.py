# coding=utf-8
"""
Report (and optionally delete) GBIF-sourced occurrences that no longer exist
upstream in GBIF.

A GET /occurrence/{gbifID} that returns 404 means GBIF no longer indexes the
occurrence (effectively deleted). In dry_run mode nothing is deleted; the task
only reports how many records would be removed. Either way a summary is emailed
to superusers, mirroring the "Clear taxa not in group" cleanup.

Records are checked oldest-modified first (see modified_date) so that, combined
with a limit, each run spends its budget on the stalest records.
"""

import csv
import io
import logging
from datetime import timedelta

import requests
from requests.adapters import HTTPAdapter, Retry
from celery import shared_task
from django.db.models import F, Q
from django.utils import timezone

from bims.utils.mail import mail_superusers, get_domain_name

logger = logging.getLogger("bims")

GBIF_API = 'https://api.gbif.org/v1'


def _build_session():
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(['GET']),
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session


def _occurrence_deleted(session, gbif_id, timeout):
    """True if GBIF no longer indexes this occurrence (404)."""
    try:
        response = session.get(
            GBIF_API + '/occurrence/%s' % gbif_id, timeout=timeout)
        return response.status_code == 404
    except requests.RequestException as e:
        logger.warning("occurrence check failed for %s: %s", gbif_id, e)
        return False


CSV_FIELDNAMES = [
    'local_id', 'name', 'gbif_id', 'dataset_key', 'modified_date',
]


def _build_csv(rows):
    """Return the CSV report of affected records as a UTF-8 string."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


@shared_task(name="bims.tasks.clear_gbif_deleted_occurrences", queue="update")
def clear_gbif_deleted_occurrences(
    dry_run: bool = True,
    stale_days: int = 30,
    limit: int = 0,
    timeout: int = 30,
) -> dict:
    """
    Check GBIF-sourced occurrences against GBIF and report/delete the ones that
    have been removed upstream.

    Records that still exist upstream have their modified_date bumped to now,
    so they rotate out of the stale window and are not re-checked on the next
    run (regardless of dry_run). Records deleted upstream are left as-is so, on
    a dry run, they keep being reported until they are actually removed.

    :param dry_run: If True, do not delete anything; only report. A CSV of the
        affected records is emailed to superusers.
    :param stale_days: Only check occurrences whose modified_date is older than
        this many days (0 = no age filter). Never-checked records (NULL
        modified_date) always qualify.
    :param limit: Max number of records to check (0 = no limit). Records are
        checked oldest-modified first.
    :param timeout: Per-request timeout in seconds.
    """
    from bims.models.biological_collection_record import (
        BiologicalCollectionRecord,
    )

    session = _build_session()
    domain_name = get_domain_name()

    qs = BiologicalCollectionRecord.objects.filter(
        source_collection__icontains='gbif',
        upstream_id__isnull=False,
    ).exclude(upstream_id='')

    if stale_days:
        cutoff = timezone.now() - timedelta(days=stale_days)
        qs = qs.filter(
            Q(modified_date__lt=cutoff) | Q(modified_date__isnull=True))

    qs = qs.order_by(F('modified_date').asc(nulls_first=True), 'id')
    if limit:
        qs = qs[:limit]

    def _mark_checked(ids):
        """
        Bump modified_date on records that still exist upstream so they rotate
        out of the stale window and are not re-checked every run. Uses update()
        to bypass save() (no side effects, no auto-restamp).
        """
        if ids:
            BiologicalCollectionRecord.objects.filter(id__in=ids).update(
                modified_date=timezone.now())

    total_checked = 0
    deleted_ids = []
    alive_ids = []
    csv_rows = []
    sample = []
    for record in qs.iterator():
        total_checked += 1
        if not _occurrence_deleted(session, record.upstream_id, timeout):
            # Still exists upstream: record it as freshly checked.
            alive_ids.append(record.id)
            if len(alive_ids) >= 5000:
                _mark_checked(alive_ids)
                alive_ids = []
            continue
        deleted_ids.append(record.id)
        name = (
            record.taxonomy.scientific_name
            if record.taxonomy else record.original_species_name
        )
        csv_rows.append({
            'local_id': record.id,
            'name': name or '',
            'gbif_id': record.upstream_id,
            'dataset_key': record.dataset_key or '',
            'modified_date': record.modified_date or '',
        })
        if len(sample) < 25:
            sample.append(
                f"{record.id}: {name or '-'} (gbifID={record.upstream_id})")

    _mark_checked(alive_ids)

    to_delete = len(deleted_ids)
    deleted = 0
    if deleted_ids and not dry_run:
        _, detail_map = BiologicalCollectionRecord.objects.filter(
            id__in=deleted_ids).delete()
        deleted = detail_map.get(
            'bims.BiologicalCollectionRecord', 0)

    result = {
        "ok": True,
        "dry_run": dry_run,
        "domain": domain_name,
        "stale_days": stale_days,
        "checked": total_checked,
        "to_delete": to_delete,
        "deleted": deleted,
        "sample_to_delete": sample,
    }

    subject = (
        f"[{domain_name}] GBIF deleted-occurrence cleanup"
        f"{' (DRY RUN)' if dry_run else ''}"
    )
    message = (
        f"GBIF deleted-occurrence cleanup completed"
        f"{' (DRY RUN – no changes made)' if dry_run else ''}.\n\n"
        f"• Stale threshold (days) : {stale_days or 'none'}\n"
        f"• Occurrences checked : {total_checked}\n"
        f"• Deleted upstream in GBIF : {to_delete}\n"
        f"• Removed locally : {deleted}\n"
        f"• Sample (up to 25) : {', '.join(sample) or '-'}\n"
    )

    # On a dry run, attach the full list of affected records as a CSV so
    # superusers can review before running the real deletion.
    attachment = None
    if dry_run and csv_rows:
        attachment = (
            'gbif_deleted_occurrences.csv',
            _build_csv(csv_rows),
            'text/csv',
        )
    mail_superusers(subject=subject, body=message, attachment=attachment)
    logger.info(message.replace("\n", " "))

    return result
