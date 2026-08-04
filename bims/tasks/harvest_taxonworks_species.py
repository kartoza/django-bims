# coding=utf-8
from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone
from django_tenants.utils import schema_context

logger = logging.getLogger(__name__)

PER_PAGE = 50


class _SessionTaxonWorksTaxaProcessor:
    def __init__(self, log_fn, base_url: str, project_token: str,
                 records_by_id: dict[int, dict],
                 otus_by_taxon_name_id: dict[int, int]):
        from bims.scripts.taxa_upload_taxonworks import SessionTaxonWorksTaxaProcessor
        self._processor = SessionTaxonWorksTaxaProcessor(
            log_fn,
            base_url=base_url,
            project_token=project_token,
            records_by_id=records_by_id,
            otus_by_taxon_name_id=otus_by_taxon_name_id,
        )

    def process(self, record: dict, taxon_group, harvest_synonyms: bool):
        return self._processor.process(
            record,
            taxon_group,
            harvest_synonyms=harvest_synonyms,
        )


@shared_task(name='bims.tasks.harvest_taxonworks_species', queue='update')
def harvest_taxonworks_species(session_id: int, schema_name: str):
    from bims.models import HarvestSession
    from bims.signals.utils import connect_bims_signals, disconnect_bims_signals
    from bims.utils.taxonworks import (
        get_taxon_names_page,
        fetch_otus_for_ids,
        taxonworks_record_is_extinct,
    )

    with schema_context(schema_name):
        try:
            session = HarvestSession.objects.get(id=session_id)
        except HarvestSession.DoesNotExist:
            logger.error("harvest_taxonworks_species: session %s not found", session_id)
            return

        def _log(msg: str):
            ts = timezone.now().isoformat(timespec="seconds")
            line = f"[{ts}] {msg}\n"
            logger.info("TaxonWorks harvest session=%s: %s", session_id, msg)
            if session.log_file:
                try:
                    with open(session.log_file.path, "a") as fh:
                        fh.write(line)
                except Exception:
                    pass

        disconnect_bims_signals()

        if not session.status or session.status == "queued":
            session.status = "Processing"
            session.save(update_fields=["status"])

        additional = session.additional_data or {}
        base_url = (additional.get("base_url") or "").strip()
        project_token = (additional.get("project_token") or "").strip()
        exclude_extinct = additional.get("exclude_extinct", True)

        if not base_url or not project_token:
            _log("Missing TaxonWorks base_url or project_token - aborting")
            HarvestSession.objects.filter(id=session_id).update(
                status="Failed: incomplete TaxonWorks config",
                finished=True,
            )
            connect_bims_signals()
            return

        _log(f"Starting TaxonWorks harvest at {base_url}")

        processed_ids: set[int] = set(
            int(x) for x in additional.get("processed_taxonworks_ids", [])
        )
        page = additional.get("current_page", 1)
        total_processed = len(processed_ids)
        latest_updated_at = additional.get("source_version_latest_updated_at")

        # Mutable caches shared with the processor across pages.
        # records_cache grows as pages are fetched; it also serves as the
        # parent-lookup cache when _ensure_taxonomy recurses up the tree.
        records_cache: dict[int, dict] = {}
        otus_cache: dict[int, int] = {}

        processor = _SessionTaxonWorksTaxaProcessor(
            _log,
            base_url=base_url,
            project_token=project_token,
            records_by_id=records_cache,
            otus_by_taxon_name_id=otus_cache,
        )

        canceled = False

        while True:
            if HarvestSession.objects.filter(id=session_id, canceled=True).exists():
                _log("Harvest canceled by user")
                canceled = True
                break

            _log(f"Fetching taxon names page {page} (per={PER_PAGE})...")
            page_records = get_taxon_names_page(
                base_url, project_token, page=page, per_page=PER_PAGE
            )
            if not page_records:
                _log("No more records")
                break

            # Extend the parent-lookup cache with this page's records.
            for r in page_records:
                if r.get("id"):
                    records_cache[int(r["id"])] = r

            # Fetch OTUs only for the taxon_name_ids on this page.
            page_ids = [int(r["id"]) for r in page_records if r.get("id")]
            page_otus = fetch_otus_for_ids(base_url, project_token, page_ids)
            otus_cache.update(page_otus)

            _log(
                f"Page {page}: {len(page_records)} taxon names, "
                f"{len(page_otus)} OTUs"
            )

            for record in page_records:
                if HarvestSession.objects.filter(id=session_id, canceled=True).exists():
                    _log("Harvest canceled by user")
                    canceled = True
                    break

                record_id = record.get("id")
                if not record_id:
                    continue
                record_id = int(record_id)

                if record_id in processed_ids:
                    continue

                if exclude_extinct and taxonworks_record_is_extinct(record):
                    _log(
                        f"Skipping extinct taxon id={record_id} "
                        f"({record.get('cached', '')})"
                    )
                    processed_ids.add(record_id)
                    continue

                try:
                    processor.process(
                        record,
                        session.module_group,
                        harvest_synonyms=session.harvest_synonyms,
                    )
                    processed_ids.add(record_id)
                    total_processed += 1
                    updated_at = record.get("updated_at")
                    if updated_at and (
                        not latest_updated_at or updated_at > latest_updated_at
                    ):
                        latest_updated_at = updated_at
                    _log(
                        f"[{total_processed}] Processed: "
                        f"{record.get('cached') or record.get('name', '')} "
                        f"({(record.get('rank') or 'unknown rank').capitalize()}, "
                        f"id={record_id})"
                    )
                except Exception as exc:
                    _log(f"Error processing TaxonWorks id={record_id}: {exc}")

            if canceled:
                break

            # Persist progress after every page so a resume starts from here.
            session.additional_data = {
                **additional,
                "base_url": base_url,
                "project_token": project_token,
                "exclude_extinct": exclude_extinct,
                "current_page": page,
                "processed_taxonworks_ids": list(processed_ids),
                "source_version_latest_updated_at": latest_updated_at,
            }
            session.status = f"Processing (page {page}, {total_processed} taxa)"
            session.save(update_fields=["additional_data", "status"])

            if len(page_records) < PER_PAGE:
                break
            page += 1

        finished_at = timezone.now().isoformat(timespec="seconds")
        final_additional_data = {
            **additional,
            "base_url": base_url,
            "project_token": project_token,
            "exclude_extinct": exclude_extinct,
            "current_page": page,
            "processed_taxonworks_ids": list(processed_ids),
            "source_version_latest_updated_at": latest_updated_at,
            "finished_at": finished_at,
        }

        if not canceled:
            _log(f"Harvest complete - {total_processed} taxa processed")
            HarvestSession.objects.filter(id=session_id).update(
                status=f"Finished ({total_processed} taxa)",
                finished=True,
                additional_data=final_additional_data,
            )
        else:
            HarvestSession.objects.filter(id=session_id).update(
                status=f"Canceled ({total_processed} taxa before cancel)",
                additional_data=final_additional_data,
            )

        connect_bims_signals()
