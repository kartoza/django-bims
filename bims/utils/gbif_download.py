import csv
import io
import json
import logging
import os
import time
import zipfile
from pathlib import Path
from typing import List, Optional, Set, Callable, Dict, Any

import requests
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

logger = logging.getLogger(__name__)

GBIF_DOWNLOAD_URL  = "https://api.gbif.org/v1/occurrence/download"
GBIF_REQUEST_URL   = f"{GBIF_DOWNLOAD_URL}/request"


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
    log: Callable[[str], None],
):
    """Recursively attach the parents of *taxon* to *group*."""
    from bims.models.taxon_group_taxonomy import TaxonGroupTaxonomy

    if taxon.parent:
        tgt, _ = TaxonGroupTaxonomy.objects.get_or_create(
            taxongroup=group, taxonomy=taxon
        )
        tgt.is_validated = validated
        tgt.save()
        add_parent_to_group(taxon.parent, group, validated, log)


def submit_download(
    gbif_user: str,
    gbif_pass: str,
    predicate: Dict[str, Any],
    description: str,
    log: Callable[[str], None],
) -> Optional[str]:
    """Fire a download request and return the GBIF download key."""
    payload = {
        "creator": gbif_user,
        "sendNotification": False,
        "format": "DWCA",
        "description": description,
        "predicate": predicate,
    }
    log(f"POST {GBIF_REQUEST_URL}")
    log(description)
    log(payload)
    r = requests.post(GBIF_REQUEST_URL, auth=(gbif_user, gbif_pass), json=payload, timeout=60)
    if r.status_code != 201:
        log(f"Download request failed ({r.status_code}): {r.text}")
        return None
    return r.text.strip().strip('"')


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
        if link:
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
                    key_val = row.get("acceptedTaxonKey") or row.get("taxonKey")
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
    gbif_username: Optional[str] = None,
    gbif_password: Optional[str] = None,
) -> List:
    """
    Return all species occurring inside *boundary_id* that descend from
    *parent_species*, using the GBIF Occurrence-Download API.
    """
    from bims.models.boundary import Boundary
    from bims.models.taxon_group import TaxonGroup
    from bims.models.taxon_group_taxonomy import TaxonGroupTaxonomy
    from bims.utils.fetch_gbif import fetch_all_species_from_gbif
    from bims.utils.gbif import round_coordinates
    from bims.scripts.import_gbif_occurrences import ACCEPTED_BASIS_OF_RECORD

    log_file_path = get_log_file_path(harvest_session)
    log = lambda m: log_with_file(m, log_file_path)

    gbif_user = gbif_username or os.getenv("GBIF_USERNAME")
    gbif_pass = gbif_password or os.getenv("GBIF_PASSWORD")
    if not gbif_user or not gbif_pass:
        raise RuntimeError("GBIF_USERNAME / GBIF_PASSWORD are required")

    auth = (gbif_user, gbif_pass)
    species_keys: Set[int] = set()
    species_found: List = []

    taxon_group: Optional[TaxonGroup] = (
        harvest_session.module_group if harvest_session else None
    )

    try:
        boundary = Boundary.objects.get(id=boundary_id)
        geometry = boundary.geometry
        if not geometry:
            raise ValueError("Boundary has no geometry")

        polygons = list(geometry) if isinstance(geometry, MultiPolygon) else [geometry]
        log(f"Found {len(polygons)} polygon(s)")

        for idx, polygon in enumerate(polygons, 1):
            if is_canceled(harvest_session) or (
                max_limit and len(species_keys) >= max_limit
            ):
                break

            geojson = json.loads(polygon.geojson)
            geojson["coordinates"] = round_coordinates(
                geojson["coordinates"])
            geom_wkt = GEOSGeometry(json.dumps(geojson)).wkt
            log(f"Polygon {idx}/{len(polygons)}")

            key = submit_download(
                gbif_user,
                gbif_pass,
                predicate={
                    "type": "and",
                    "predicates": [
                        {"type": "equals", "key": "TAXON_KEY", "value": str(parent_species.gbif_key)},
                        {"type": "within", "geometry": geom_wkt},
                        {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
                        {"type": "equals", "key": "HAS_GEOSPATIAL_ISSUE", "value": "false"},
                        {"type": "in", "key": "BASIS_OF_RECORD", "values": ACCEPTED_BASIS_OF_RECORD},
                    ],
                },
                description=f"Boundary {boundary_id} · parent {parent_species.scientific_name}",
                log=log,
            )
            if not key:
                continue

            zip_url = get_ready_download_url(key, auth, log, lambda: is_canceled(harvest_session))
            if not zip_url:
                log(f"Download {key} was not completed")
                continue

            zip_path = download_archive(zip_url, key, auth, log)
            if not zip_path:
                continue

            extract_species_keys(zip_path, species_keys, max_limit, log)
            log(f"Unique species keys: {len(species_keys)}")

            if max_limit and len(species_keys) >= max_limit:
                break

    except Boundary.DoesNotExist:
        logger.error(f"Boundary {boundary_id} does not exist.")
        return []
    except Exception as exc:
        logger.error(f"Boundary processing failed: {exc}")
        return []

    for skey in species_keys:
        if is_canceled(harvest_session):
            break
        try:
            log(f"Processing {skey}")
            taxonomy = fetch_all_species_from_gbif(
                gbif_key=skey,
                fetch_children=False,
                log_file_path=log_file_path,
                fetch_vernacular_names=True,
            )
            if taxonomy:
                species_found.append(taxonomy)
                if taxon_group:
                    tgt, _ = TaxonGroupTaxonomy.objects.get_or_create(
                        taxongroup=taxon_group, taxonomy=taxonomy
                    )
                    tgt.is_validated = validated
                    tgt.save()
                    add_parent_to_group(taxonomy, taxon_group, validated, log)
        except Exception as exc:
            log(f"Error fetching taxonomy {skey}: {exc}")

    log(f"Species found: {len(species_found)}")
    return species_found
