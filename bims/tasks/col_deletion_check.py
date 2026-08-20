# coding=utf-8
"""Celery task backing the async CoL/GBIF deletion check on the Taxa
Data Quality page.

Detection logic (batch POST to /v2/species/match, GET fallback,
deleted/stale/unchanged classification) mirrors
bims/management/commands/check_col_deletions.py, but only acts on
status == 'deleted' findings and persists progress/results to
DataUpstreamDeletionCheckSession / DataUpstreamDeletionCheckResult so the Taxa
Data Quality page can show a progress bar and a results table.
"""
import logging

import requests
from celery import shared_task
from django.utils import timezone
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


def build_session():
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(['GET', 'POST']),
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session


def match_one_get(session, match_url, checklist_key, taxon, timeout):
    try:
        response = session.get(
            match_url,
            params={'usageKey': taxon.col_id, 'checklistKey': checklist_key},
            timeout=timeout,
        )
        if not response.ok:
            return None
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning(
            'match_one_get failed for col_id=%s: %s', taxon.col_id, exc)
        return None


def evaluate(taxon, data):
    """Return 'deleted' if the taxon's col_id no longer resolves on COL,
    else None (unchanged / stale_key / error are out of scope here)."""
    if data is None:
        return None

    diagnostics = data.get('diagnostics') or {}
    match_type = diagnostics.get('matchType')
    usage = data.get('usage') or {}

    if match_type in (None, 'NONE') or not usage:
        return 'COL /species/match returned no usage for this col_id.'

    return None


@shared_task(name='bims.tasks.check_col_deletions', queue='update')
def check_col_deletions_task(session_id):
    from django.contrib.contenttypes.models import ContentType

    from bims.models.upstream_deletion_check import (
        DataUpstreamDeletionCheckResult,
        DataUpstreamDeletionCheckSession,
    )
    from bims.models.taxonomy import Taxonomy
    from bims.utils.col import COL_CHECKLIST_KEY, GBIF_API_V2
    from bims.views.taxa_validation import query_taxa

    taxonomy_content_type = ContentType.objects.get_for_model(Taxonomy)

    match_url = f'{GBIF_API_V2}/species/match'
    timeout = 30

    try:
        check_session = DataUpstreamDeletionCheckSession.objects.get(id=session_id)
    except DataUpstreamDeletionCheckSession.DoesNotExist:
        logger.warning('DataUpstreamDeletionCheckSession %s does not exist', session_id)
        return

    check_session.status = 'running'
    check_session.started_at = timezone.now()
    check_session.save(update_fields=['status', 'started_at'])

    try:
        qs = query_taxa(check_session.taxon_group_id).filter(
            col_id__isnull=False,
        ).exclude(col_id='').order_by('id')

        total = qs.count()
        check_session.total = total
        check_session.save(update_fields=['total'])

        http_session = build_session()

        processed = 0
        found_count = 0
        removed_count = 0

        offset = 0
        while offset < total:
            is_canceled = DataUpstreamDeletionCheckSession.objects.filter(
                id=session_id).values_list('canceled', flat=True).first()
            if is_canceled:
                check_session.status = 'canceled'
                check_session.finished_at = timezone.now()
                check_session.save(update_fields=['status', 'finished_at'])
                return

            batch = list(qs[offset:offset + BATCH_SIZE])
            if not batch:
                break

            results = None

            if results is None:
                results = [
                    match_one_get(
                        http_session, match_url, COL_CHECKLIST_KEY,
                        taxon, timeout)
                    for taxon in batch
                ]

            for taxon, data in zip(batch, results):
                processed += 1
                detail = evaluate(taxon, data)
                if detail is None:
                    continue

                found_count += 1
                result, _ = DataUpstreamDeletionCheckResult.objects.update_or_create(
                    session=check_session,
                    content_type=taxonomy_content_type,
                    object_id=str(taxon.id),
                    defaults={
                        'name': taxon.canonical_name or '',
                        'upstream_id': taxon.col_id,
                        'detail': detail,
                    },
                )

                if check_session.auto_remove:
                    taxon.col_id = None
                    taxon.save(update_fields=['col_id'])
                    result.removed = True
                    result.removed_auto = True
                    result.removed_at = timezone.now()
                    result.save(
                        update_fields=['removed', 'removed_auto', 'removed_at'])
                    removed_count += 1

            offset += BATCH_SIZE

            check_session.processed = processed
            check_session.found_count = found_count
            check_session.removed_count = removed_count
            check_session.last_progress_update = timezone.now()
            check_session.save(update_fields=[
                'processed', 'found_count', 'removed_count',
                'last_progress_update',
            ])

        check_session.status = 'completed'
        check_session.finished_at = timezone.now()
        check_session.save(update_fields=['status', 'finished_at'])
    except Exception as exc:
        check_session.status = 'failed'
        check_session.error_message = str(exc)
        check_session.finished_at = timezone.now()
        check_session.save(
            update_fields=['status', 'error_message', 'finished_at'])
        raise
