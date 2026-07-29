import csv
import io
import json
import logging
import os
import tempfile
import time
import zipfile
from pathlib import Path
from typing import List, Optional, Set, Callable, Dict, Any, Tuple

import requests
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.db import connection, transaction
from preferences import preferences

from bims.templatetags import is_fada_site

logger = logging.getLogger(__name__)

GBIF_DOWNLOAD_URL  = "https://api.gbif.org/v1/occurrence/download"
GBIF_REQUEST_URL   = f"{GBIF_DOWNLOAD_URL}/request"
SIDECAR_DIR = os.path.join(settings.MEDIA_ROOT, "harvest-session-log")


def _resume_load(harvest_session) -> dict:
    if not harvest_session or not harvest_session.status:
        return {}
    try:
        data = json.loads(harvest_session.status)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _resume_save(harvest_session, state: dict):
    if not harvest_session:
        return
    harvest_session.status = json.dumps(state, separators=(",", ":"), ensure_ascii=False)
    try:
        with transaction.atomic():
            harvest_session.save(update_fields=["status"])
    except Exception:
        logging.getLogger(__name__).exception("Failed saving resume state")


def _resume_clear(harvest_session):
    if not harvest_session:
        return
    try:
        harvest_session.status = ""
        harvest_session.save(update_fields=["status"])
    except Exception:
        logging.getLogger(__name__).exception("Failed clearing resume state")


def _species_sidecar_path(harvest_session) -> Optional[str]:
    if not harvest_session:
        return None
    os.makedirs(SIDECAR_DIR, exist_ok=True)
    tenant = connection.schema_name
    return os.path.join(SIDECAR_DIR, f"{tenant}_{harvest_session.id}_species.json")


def _species_load_set(harvest_session) -> Set[int]:
    """Load species keys from sidecar file into a Python set."""
    path = _species_sidecar_path(harvest_session)
    if not path or not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh) or []
            return set(int(x) for x in data)
    except Exception:
        logging.getLogger(__name__).exception("Failed reading species sidecar")
        return set()


def _species_count(harvest_session) -> int:
    path = _species_sidecar_path(harvest_session)
    if not path or not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh) or []
            return len(data)
    except Exception:
        logging.getLogger(__name__).exception("Failed counting species sidecar")
        return 0


def _species_write_set(harvest_session, keys: Set[int]):
    """Atomic write of the full set to sidecar JSON."""
    path = _species_sidecar_path(harvest_session)
    if not path:
        return
    tmp_fd, tmp_path = tempfile.mkstemp(prefix="sp_", suffix=".json", dir=SIDECAR_DIR)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(sorted(keys), fh, separators=(",", ":"))
        os.replace(tmp_path, path)
    except Exception:
        logging.getLogger(__name__).exception("Failed writing species sidecar")
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def _species_reset(harvest_session):
    """Clear sidecar file (used if boundary/parent changes)."""
    path = _species_sidecar_path(harvest_session)
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            logging.getLogger(__name__).exception("Failed removing species sidecar")


def _col_ids_sidecar_path(harvest_session) -> Optional[str]:
    if not harvest_session:
        return None
    os.makedirs(SIDECAR_DIR, exist_ok=True)
    tenant = connection.schema_name
    return os.path.join(SIDECAR_DIR, f"{tenant}_{harvest_session.id}_col_ids.json")


def _col_ids_load_map(harvest_session) -> Dict[str, dict]:
    """Load {col_id: row_data} map from sidecar. row_data may be {} if harvested from occurrence download."""
    path = _col_ids_sidecar_path(harvest_session)
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh) or {}
            return data if isinstance(data, dict) else {}
    except Exception:
        logging.getLogger(__name__).exception("Failed reading col_ids sidecar")
        return {}


def _col_ids_write_map(harvest_session, col_ids: Dict[str, dict]):
    path = _col_ids_sidecar_path(harvest_session)
    if not path:
        return
    tmp_fd, tmp_path = tempfile.mkstemp(prefix="col_", suffix=".json", dir=SIDECAR_DIR)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(col_ids, fh, separators=(",", ":"))
        os.replace(tmp_path, path)
    except Exception:
        logging.getLogger(__name__).exception("Failed writing col_ids sidecar")
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def _col_ids_reset(harvest_session):
    path = _col_ids_sidecar_path(harvest_session)
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            logging.getLogger(__name__).exception("Failed removing col_ids sidecar")


def _species_add_from_dwca(
        zip_path: Path,
        harvest_session,
        max_limit: Optional[int], log: Callable[[str], None]) -> int:
    """
    Read occurrence.txt and add taxonKey/acceptedTaxonKey to sidecar.
    When taxonKey is alphanumeric (COL ID from a checklist download), it is
    stored in the col_ids sidecar instead of the numeric species sidecar.
    Flush to disk at the end (and optionally mid-stream if many new).
    Return the new total count.
    """
    keys = _species_load_set(harvest_session)
    col_ids = _col_ids_load_map(harvest_session)
    before = len(keys) + len(col_ids)
    added_since_flush = 0
    try:
        with zipfile.ZipFile(zip_path) as zf:
            with zf.open("occurrence.txt") as occ_file:
                txt = io.TextIOWrapper(occ_file, encoding="utf-8")
                header = txt.readline().rstrip("\n\r").split("\t")
                reader = csv.DictReader(txt, fieldnames=header, delimiter="\t")
                for row in reader:
                    key_val = row.get("taxonKey") or row.get("acceptedTaxonKey")
                    if not key_val:
                        continue
                    if key_val.isdigit():
                        k = int(key_val)
                        if k not in keys:
                            keys.add(k)
                            added_since_flush += 1
                    else:
                        if key_val not in col_ids:
                            col_ids[key_val] = {}
                            added_since_flush += 1
                    if added_since_flush >= 500:
                        _species_write_set(harvest_session, keys)
                        _col_ids_write_map(harvest_session, col_ids)
                        added_since_flush = 0
                    total = len(keys) + len(col_ids)
                    if max_limit and total >= max_limit:
                        break
    except Exception as exc:
        log(f"Could not read {zip_path}: {exc}")

    _species_write_set(harvest_session, keys)
    _col_ids_write_map(harvest_session, col_ids)
    after = len(keys) + len(col_ids)
    if after != before:
        log(f"Sidecar updated: +{after - before} (total={after})")
    return after


def _species_add_from_species_list(
        zip_path: Path,
        harvest_session,
        max_limit: Optional[int], log: Callable[[str], None]) -> int:
    """
    Read csv from a SPECIES_LIST download and add taxonKey values to sidecar.
    Numeric keys go to the species sidecar; alphanumeric COL IDs go to the col_ids sidecar.
    Return the new total count.
    """
    col_ids = _col_ids_load_map(harvest_session)
    before = len(col_ids)
    added_since_flush = 0
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            data_file = next(
                (n for n in names if n.endswith('.csv')),
                None
            )
            if not data_file:
                log(f"No .csv data file found in species list archive: {names}")
                return _species_count(harvest_session) + len(_col_ids_load_map(harvest_session))
        with zipfile.ZipFile(zip_path) as zf:
            with zf.open(data_file) as sp_file:
                txt = io.TextIOWrapper(sp_file, encoding="utf-8")
                header = txt.readline().rstrip("\n\r").split("\t")
                reader = csv.DictReader(txt, fieldnames=header, delimiter="\t")
                for row in reader:
                    key_val = row.get("taxonKey") or row.get("acceptedTaxonKey")
                    if not key_val:
                        continue
                    if key_val not in col_ids:
                        col_ids[key_val] = dict(row)
                        added_since_flush += 1
                    if added_since_flush >= 500:
                        _col_ids_write_map(harvest_session, col_ids)
                        added_since_flush = 0
                    total = len(col_ids)
                    if max_limit and total >= max_limit:
                        break
    except Exception as exc:
        log(f"Could not read species list from {zip_path}: {exc}")

    _col_ids_write_map(harvest_session, col_ids)
    after = len(col_ids)
    if after != before:
        log(f"Species list sidecar updated: +{after - before} (total={after})")
    return after


def _submit_with_retry(
        gbif_user,
        gbif_pass, predicate, description, log, harvest_session, max_retries=10, wait_seconds=5*60,
        checklist_key=None, download_format="DWCA"):
    key, status_code = submit_download(
        gbif_user, gbif_pass, predicate=predicate, description=description, log=log,
        checklist_key=checklist_key, download_format=download_format)
    attempt = 0
    while (not key) and status_code == 429 and attempt < max_retries:
        attempt += 1
        log(f"GBIF rate-limited (429). Retrying in 5 minutes... attempt {attempt}/{max_retries}")
        waited = 0
        step = 5
        while waited < wait_seconds:
            if is_canceled(harvest_session):
                log("Harvest canceled during backoff wait.")
                return None
            time.sleep(step)
            waited += step
        key, status_code = submit_download(
            gbif_user, gbif_pass, predicate=predicate, description=description, log=log,
            checklist_key=checklist_key, download_format=download_format)
    if not key:
        log(f"Download request failed (status_code={status_code})")
        return None
    return key


def get_log_file_path(harvest_session) -> Optional[str]:
    """Return a writable path for HarvestSession.log_file or *None*."""
    if not harvest_session:
        return None
    try:
        lf = harvest_session.log_file
        return lf.path if lf and lf.name else None
    except ValueError:
        return None


def log_with_file(message: str, log_file_path: Optional[str]):
    """Write to std logger and (optionally) append to the harvest log file."""
    logger.info(message)
    if log_file_path:
        try:
            with open(log_file_path, "a") as fh:
                fh.write(f"{message}\n")
        except Exception:
            logger.exception("Unable to write harvest log")


def is_canceled(harvest_session) -> bool:
    """Fresh-check the DB row each time to see if the job was canceled."""
    if not harvest_session:
        return False
    from bims.models import HarvestSession
    return HarvestSession.objects.filter(
        id=harvest_session.id, canceled=True).exists()


def add_parent_to_group(
    taxon,
    group,
    validated: bool,
    log: Optional[Callable[[str], None]] = None,
    *,
    include_self: bool = True,
    max_steps: int = 200,
):
    """
    Attach `taxon` (optionally) and all its parents to `group` safely.
    """
    from django.db import transaction
    from bims.models.taxon_group_taxonomy import TaxonGroupTaxonomy

    def _log(msg: str) -> None:
        if log:
            try:
                log(msg)
            except Exception:
                pass

    visited_ids = set()
    chain = []
    current = taxon if include_self else getattr(taxon, "parent", None)
    steps = 0

    while current and steps < max_steps:
        if current.id in visited_ids:
            _log(f"[add_parent_to_group] Cycle detected at taxon #{current.id}; stopping.")
            break
        visited_ids.add(current.id)
        chain.append(current)
        steps += 1
        current = getattr(current, "parent", None)

    if steps >= max_steps:
        _log(f"[add_parent_to_group] Stopped after {steps} steps (max_steps={max_steps}).")

    if not chain:
        return

    taxonomy_ids = [t.id for t in chain]

    with transaction.atomic():
        existing_ids = set(
            TaxonGroupTaxonomy.objects
            .filter(taxongroup=group, taxonomy_id__in=taxonomy_ids)
            .values_list("taxonomy_id", flat=True)
        )

        to_create = [
            TaxonGroupTaxonomy(
                taxongroup=group,
                taxonomy_id=tid,
                is_validated=validated,
            )
            for tid in taxonomy_ids
            if tid not in existing_ids
        ]
        if to_create:
            TaxonGroupTaxonomy.objects.bulk_create(to_create, ignore_conflicts=True)

        if existing_ids:
            (TaxonGroupTaxonomy.objects
             .filter(taxongroup=group, taxonomy_id__in=list(existing_ids))
             .exclude(is_validated=validated)
             .update(is_validated=validated))

    _log(f"[add_parent_to_group] Linked {len(taxonomy_ids)} taxa "
         f"({len(taxonomy_ids) - len(existing_ids)} created, {len(existing_ids)} existed).")


def submit_download(
    gbif_user: str,
    gbif_pass: str,
    predicate: Dict[str, Any],
    description: str,
    log: Callable[[str], None],
    checklist_key: Optional[str] = None,
    download_format: str = "DWCA",
) -> Tuple[Optional[str], Any]:
    """Fire a download request and return the GBIF download key."""
    payload = {
        "creator": gbif_user,
        "sendNotification": False,
        "format": download_format,
        "description": description,
        "predicate": predicate,
    }
    if checklist_key:
        payload["checklistKey"] = checklist_key
    log(f"POST {GBIF_REQUEST_URL}")
    log(description)
    r = requests.post(GBIF_REQUEST_URL, auth=(gbif_user, gbif_pass), json=payload, timeout=60)
    if r.status_code != 201:
        log(f"Download request failed ({r.status_code}): {r.text}")
        return None, r.status_code
    return r.text.strip().strip('"'), r.status_code


def get_download_information(
    key: str,
) -> Any:
    download_url = f'{GBIF_DOWNLOAD_URL}/{key}'
    resp = requests.get(download_url, timeout=30)
    if resp.status_code != 200:
        return ""
    info = resp.json()
    return info


def get_ready_download_url(
    key: str,
    auth,
    log: Callable[[str], None],
    cancel_cb: Callable[[], bool],
) -> Optional[str]:
    """Poll until a working ZIP URL is available or we are cancelled."""
    status_url = f"{GBIF_DOWNLOAD_URL}/{key}"
    while not cancel_cb():
        resp = requests.get(status_url, auth=auth, timeout=30)
        if resp.status_code != 200:
            log(f"Status check failed ({resp.status_code}): {resp.text}")
            return None
        info   = resp.json()
        status = info.get("status", "UNKNOWN")
        link   = info.get("downloadLink")
        log(f"{key} status={status} link={link}")
        if status in {"FAILED", "KILLED", "CANCELLED"}:
            return None
        if status == "SUCCEEDED":
            probe = requests.get(link, auth=auth, stream=True, timeout=60)
            if probe.status_code == 200:
                probe.close()
                return link
        time.sleep(30)
    return None


def download_archive(
    zip_url: str,
    key: str,
    auth,
    log: Callable[[str], None],
) -> Optional[Path]:
    """Save the GBIF DWCA zip under MEDIA_ROOT/gbif_downloads/{key}.zip."""
    target_dir  = Path(settings.MEDIA_ROOT) / "gbif_downloads"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{key}.zip"

    if target_path.exists():
        log(f"Archive cached → {target_path}")
        return target_path

    log(f"Downloading {zip_url}")
    try:
        with requests.get(zip_url, auth=auth, stream=True, timeout=300) as resp:
            resp.raise_for_status()
            with open(target_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    fh.write(chunk)
        log(f"Saved to {target_path}")
        return target_path
    except Exception as exc:
        log(f"Failed to download archive {key}: {exc}")
        target_path.unlink(missing_ok=True)
        return None


def extract_species_keys(
    zip_path: Path,
    species_keys: Set[int],
    max_limit: Optional[int],
    log: Callable[[str], None],
):
    """Populate *species_keys* from occurrence.txt in the DWCA."""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            with zf.open("occurrence.txt") as occ_file:
                txt = io.TextIOWrapper(occ_file, encoding="utf-8")
                header = txt.readline().rstrip("\n\r").split("\t")
                reader = csv.DictReader(txt, fieldnames=header, delimiter="\t")
                for row in reader:
                    key_val = row.get("taxonKey") or row.get("acceptedTaxonKey")
                    if key_val and key_val.isdigit():
                        species_keys.add(int(key_val))
                        if max_limit and len(species_keys) >= max_limit:
                            break
    except Exception as exc:
        log(f"Could not read {zip_path}: {exc}")

def find_species_by_area(
    boundary_id: int,
    parent_species,
    max_limit: Optional[int] = None,
    harvest_session=None,
    validated: bool = True,
) -> List:
    """
    Resumable species harvest (by boundary) that persists keys to a sidecar JSON file.
    """
    from bims.models.boundary import Boundary
    from bims.models.taxon_group import TaxonGroup
    from bims.models.taxon_group_taxonomy import TaxonGroupTaxonomy
    from bims.utils.fetch_gbif import fetch_all_species_from_gbif, harvest_synonyms_for_accepted_taxonomy
    from bims.utils.col import resolve_col_id, COL_CHECKLIST_KEY
    from bims.utils.gbif import round_coordinates
    from bims.utils.audit import disable_easy_audit
    from bims.scripts.import_gbif_occurrences import ACCEPTED_BASIS_OF_RECORD
    from bims.scripts.import_gbif_occurrences import (
        DATE_ISSUES_TO_EXCLUDE, chunked, BOUNDARY_BATCH_SIZE,
        _clean_polygonal, _union_polys, _enforce_ccw_exteriors,
        get_ready_download_url, download_archive
    )

    log_file_path = get_log_file_path(harvest_session)
    log = lambda m: log_with_file(m, log_file_path)
    harvest_synonyms = harvest_session.harvest_synonyms if harvest_session else False

    gbif_user = preferences.SiteSetting.gbif_username
    gbif_pass = preferences.SiteSetting.gbif_password
    if not gbif_user or not gbif_pass:
        raise RuntimeError("GBIF_USERNAME / GBIF_PASSWORD are required")

    auth = (gbif_user, gbif_pass)
    taxon_group: Optional[TaxonGroup] = (harvest_session.module_group if harvest_session else None)

    state = _resume_load(harvest_session)
    state.setdefault("next_batch", 1)
    state.setdefault("download_keys", {})
    state.setdefault("meta", {})

    try:
        boundary = Boundary.objects.get(id=boundary_id)
    except Boundary.DoesNotExist:
        logger.error(f"Boundary {boundary_id} does not exist.")
        return []

    geometry = boundary.geometry
    if not geometry:
        logger.error("Boundary has no geometry")
        return []

    extracted_polygons = list(geometry) if isinstance(geometry, MultiPolygon) else [geometry]
    batches = list(chunked(extracted_polygons, BOUNDARY_BATCH_SIZE))
    total_batches = len(batches)

    scope_changed = (
        state["meta"].get("boundary_id") != boundary_id
        or state["meta"].get("parent_key") != getattr(parent_species, "col_id", None)
        or state["meta"].get("polygon_count") != len(extracted_polygons)
        or state["meta"].get("batch_size") != BOUNDARY_BATCH_SIZE
    )
    if scope_changed:
        _species_reset(harvest_session)
        _col_ids_reset(harvest_session)
        state = {
            "next_batch": 1,
            "download_keys": {},
            "meta": {
                "boundary_id": boundary_id,
                "parent_key": getattr(parent_species, "col_id", None),
                "polygon_count": len(extracted_polygons),
                "batch_size": BOUNDARY_BATCH_SIZE,
            },
        }
        _resume_save(harvest_session, state)

    current_count = _species_count(harvest_session)
    log(f"Found {len(extracted_polygons)} polygon(s); "
        f"batches={total_batches}; "
        f"resuming at batch {state['next_batch']}; "
        f"current species in sidecar={current_count}")

    start_idx = max(1, int(state["next_batch"]))
    for batch_no in range(start_idx, total_batches + 1):
        if is_canceled(harvest_session):
            break
        if max_limit and _species_count(harvest_session) >= max_limit:
            break

        poly_batch = batches[batch_no - 1]

        cleaned_parts = []
        for poly in poly_batch:
            gj = json.loads(poly.geojson)
            gj["coordinates"] = round_coordinates(gj["coordinates"])
            g = GEOSGeometry(json.dumps(gj))
            g = _clean_polygonal(g)
            if g is None:
                log("Skipped an invalid polygon after cleaning")
                continue
            cleaned_parts.extend(list(g))

        if not cleaned_parts:
            log(f"Batch {batch_no}: no valid polygons after cleaning. Skipping.")
            state["next_batch"] = batch_no + 1
            _resume_save(harvest_session, state)
            continue

        multi = _union_polys(cleaned_parts)
        multi = _clean_polygonal(multi) if multi is not None else None
        if multi is None:
            log(f"Batch {batch_no}: union/clean failed. Skipping.")
            state["next_batch"] = batch_no + 1
            _resume_save(harvest_session, state)
            continue

        multi = _enforce_ccw_exteriors(multi)
        multi = _clean_polygonal(multi)
        if multi is None:
            log(f"Batch {batch_no}: invalid geometry after orientation fix. Skipping.")
            state["next_batch"] = batch_no + 1
            _resume_save(harvest_session, state)
            continue

        geometry_str = multi.wkt

        existing_key = state["download_keys"].get(str(batch_no))
        if existing_key:
            key = existing_key
            log(f"Batch {batch_no}: reusing GBIF key {key}")
        else:
            predicate = {
                "type": "and",
                "predicates": [
                    {"type": "equals", "key": "TAXON_KEY", "value": (
                        str(parent_species.col_id) if parent_species.col_id else str(parent_species.gbif_key)
                    ), "checklistKey": COL_CHECKLIST_KEY},
                    {"type": "equals", "key": "OCCURRENCE_STATUS", "value": "PRESENT"},
                    {"type": "within", "geometry": geometry_str},
                    {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
                    {"type": "equals", "key": "HAS_GEOSPATIAL_ISSUE", "value": "false"},
                    {"type": "in", "key": "BASIS_OF_RECORD", "values": ACCEPTED_BASIS_OF_RECORD},
                    {
                        "type": "not",
                        "predicate": {
                            "type": "in",
                            "key": "ISSUE",
                            "values": DATE_ISSUES_TO_EXCLUDE,
                        },
                    },
                ],
            }
            log(predicate)
            desc = (
                f"Boundary {boundary_id} · "
                f"parent {parent_species.scientific_name} · "
                f"batch {batch_no}/{total_batches}"
            )
            key = _submit_with_retry(
                gbif_user, gbif_pass, predicate, desc, log, harvest_session,
                checklist_key=COL_CHECKLIST_KEY, download_format="SPECIES_LIST")
            if not key:
                log(f"Batch {batch_no}: failed to obtain GBIF key. Will retry next run.")
                _resume_save(harvest_session, state)
                continue
            state["download_keys"][str(batch_no)] = key
            _resume_save(harvest_session, state)
            if harvest_session:
                harvest_session.additional_data = harvest_session.additional_data or {}
                harvest_session.additional_data['gbif_download_keys'] = state['download_keys']
                harvest_session.additional_data['gbif_download_meta'] = state.get('meta', {})
                harvest_session.save(update_fields=['additional_data'])

        zip_url = get_ready_download_url(key, auth, log, lambda: is_canceled(harvest_session))
        if not zip_url:
            log(f"Batch {batch_no}: GBIF key {key} not ready/failed. Will retry next run.")
            _resume_save(harvest_session, state)
            continue

        zip_path = download_archive(zip_url, key, auth, log)
        if not zip_path:
            log(f"Batch {batch_no}: download failed for key {key}. Will retry next run.")
            _resume_save(harvest_session, state)
            continue

        total_after = _species_add_from_species_list(zip_path, harvest_session, max_limit, log)
        log(f"Batch {batch_no}: unique species keys so far = {total_after}")

        state["next_batch"] = batch_no + 1
        _resume_save(harvest_session, state)

        if max_limit and total_after >= max_limit:
            break

    species_found: List = []
    col_ids_now = _col_ids_load_map(harvest_session)
    for col_id_val, col_row in col_ids_now.items():
        if is_canceled(harvest_session):
            break
        try:
            with disable_easy_audit():
                log(f"Processing COL ID {col_id_val}")
                taxonomy = fetch_all_species_from_gbif(
                    col_id=col_id_val,
                    col_row=col_row or None,
                    fetch_children=False,
                    log_file_path=log_file_path,
                    fetch_vernacular_names=True,
                )
                if not taxonomy:
                    continue
                species_found.append(taxonomy)
                if taxon_group:
                    tgt, _ = TaxonGroupTaxonomy.objects.get_or_create(
                        taxongroup=taxon_group, taxonomy=taxonomy
                    )
                    tgt.is_validated = validated
                    tgt.save()
                    add_parent_to_group(taxonomy, taxon_group, validated, log)
        except Exception as exc:
            log(f"Error processing COL ID {col_id_val}: {exc}")

    log(f"Species found: {len(species_found)}")
    return species_found
