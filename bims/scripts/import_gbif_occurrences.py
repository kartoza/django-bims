import csv
import io
import json
import datetime
import logging
import os
import time
import zipfile
from pathlib import Path
from typing import Tuple, Optional, List

import requests
from dateutil.parser import parse
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, MultiPolygon, GEOSGeometry
from django.contrib.gis.measure import D

from bims.utils.gbif_download import submit_download, get_ready_download_url, is_canceled, download_archive
from geonode.people.models import Profile
from preferences import preferences

from bims.models import (
    LocationSite,
    LocationType,
    BiologicalCollectionRecord,
    collection_post_save_handler,
    HarvestSession,
    SourceReferenceDatabase,
    Boundary,
    Dataset, Taxonomy
)
from bims.models.source_reference import DatabaseRecord
from bims.models.location_site import generate_site_code
from bims.models.survey import Survey
from bims.scripts.extract_dataset_keys import create_dataset_from_gbif
from bims.utils.gbif import round_coordinates, ACCEPTED_TAXON_KEY

logger = logging.getLogger('bims')

# Constants
UPSTREAM_ID_KEY = 'gbifID'
LON_KEY = 'decimalLongitude'
LAT_KEY = 'decimalLatitude'
COORDINATE_UNCERTAINTY_KEY = 'coordinateUncertaintyInMeters'
EVENT_DATE_KEY = 'eventDate'
COLLECTOR_KEY = 'recordedBy'
INSTITUTION_CODE_KEY = 'institutionCode'
REFERENCE_KEY = 'references'
VERBATIM_LOCALITY_KEY = 'verbatimLocality'
LOCALITY_KEY = 'locality'
SPECIES_KEY = 'species'
DATASET_KEY = 'datasetKey'
TAXON_KEY = 'taxonKey'
MODIFIED_DATE_KEY = 'modified'
DEFAULT_LOCALITY = 'No locality, from GBIF'
MISSING_KEY_ERROR = 'Missing taxon GBIF key'

API_BASE_URL = 'http://api.gbif.org/v1/occurrence/search'
DEFAULT_LIMIT = 300
LIMIT = 20  # Seems unused but kept if you still need it.
LOG_TEMPLATE = (
    '---------------------------------------------------\n'
    'Fetching: {}\n'
)

ACCEPTED_BASIS_OF_RECORD = [
    'PRESERVED_SPECIMEN',
    'OBSERVATION',
    'HUMAN_OBSERVATION',
    'MACHINE_OBSERVATION',
    'MATERIAL_SAMPLE',
    'LITERATURE',
    'MATERIAL_CITATION',
    'OCCURRENCE'
]

DATE_ISSUES_TO_EXCLUDE = [
    "RECORDED_DATE_INVALID",
    "RECORDED_DATE_MISMATCH",
    "RECORDED_DATE_UNLIKELY",
    "MODIFIED_DATE_INVALID"
]
BOUNDARY_BATCH_SIZE = 10


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def _clean_polygonal(g):
    """
    Return a valid polygonal GEOSGeometry (Polygon or MultiPolygon) or None.
    Uses make_valid() when available, falls back to buffer(0) trick.
    Also strips Z/M by re-parsing WKT.
    """
    if g is None or g.empty:
        return None
    if g.srid is None:
        g.srid = 4326
    g = GEOSGeometry(g.wkt, srid=g.srid)
    try:
        if hasattr(g, "make_valid"):
            g = g.make_valid()
    except Exception:
        pass
    if not g.valid:
        try:
            g = g.buffer(0)
        except Exception:
            return None
    if g.empty:
        return None
    if g.geom_type == "Polygon":
        return MultiPolygon(g)
    if g.geom_type == "MultiPolygon":
        return g
    if g.geom_type == "GeometryCollection":
        polys = [ge for ge in g if ge.geom_type == "Polygon"]
        if not polys:
            return None
        return MultiPolygon(polys)
    return None


def _union_polys(polys):
    """
    Robust union without relying on cascaded_union/unary_union availability.
    Accepts a list of Polygon/MultiPolygon and returns a valid MultiPolygon.
    """
    acc = None
    for p in polys:
        if acc is None:
            acc = p
        else:
            acc = acc.union(p)
        acc = _clean_polygonal(acc)
        if acc is None:
            return None
    return acc


def _ring_area(coords):
    """Signed area; >0 = CCW, <0 = CW. coords must be closed [ [x,y], ... , [x0,y0] ]."""
    area = 0.0
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        area += (x1 * y2) - (x2 * y1)
    return area / 2.0


def _ensure_closed(coords):
    """Close ring if not closed."""
    if not coords:
        return coords
    if coords[0] != coords[-1]:
        coords = coords + [coords[0]]
    return coords


def _orient_polygon_coords(poly_coords):
    """
    Enforce exteriors CCW and holes CW, in-place on a polygon's coordinates:
    poly_coords = [ exterior_ring, hole1, hole2, ... ]
    """
    if not poly_coords:
        return poly_coords

    ext = _ensure_closed(poly_coords[0])
    if _ring_area(ext) < 0:
        ext = ext[::-1]
    poly_coords[0] = ext

    for i in range(1, len(poly_coords)):
        hole = _ensure_closed(poly_coords[i])
        if _ring_area(hole) > 0:
            hole = hole[::-1]
        poly_coords[i] = hole

    return poly_coords


def _enforce_ccw_exteriors(geom):
    """
    Return a geometry with exteriors CCW and interiors CW.
    Accepts Polygon or MultiPolygon GEOSGeometry. Returns MultiPolygon.
    """
    if geom is None or geom.empty:
        return geom

    g2 = GEOSGeometry(geom.wkt, srid=geom.srid)

    gj = json.loads(g2.geojson)
    if gj["type"] == "Polygon":
        gj["coordinates"] = _orient_polygon_coords(gj["coordinates"])
        oriented = GEOSGeometry(json.dumps(gj), srid=g2.srid)
        return MultiPolygon(oriented)

    if gj["type"] == "MultiPolygon":
        for i in range(len(gj["coordinates"])):
            gj["coordinates"][i] = _orient_polygon_coords(gj["coordinates"][i])
        oriented = GEOSGeometry(json.dumps(gj), srid=g2.srid)
        return oriented

    return geom


def setup_logger(log_file_path):
    """
    Set up a logger that writes the FULL log to a single file (no rotation).
    """
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    harvest_logger = logging.getLogger('harvest_logger')
    harvest_logger.setLevel(logging.INFO)
    harvest_logger.propagate = False

    if harvest_logger.handlers:
        harvest_logger.handlers.clear()

    handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    harvest_logger.addHandler(handler)
    return harvest_logger


def log_to_file_or_logger(log_file_path, message, is_error=False):
    """
    Log messages to the 'harvest_logger' logger.
    If the logger has no handlers and log_file_path is provided, set it up.
    """
    harvest_logger = logging.getLogger('harvest_logger')
    if not harvest_logger.handlers and log_file_path:
        setup_logger(log_file_path)

    if is_error:
        harvest_logger.error(message)
    else:
        harvest_logger.info(message)


def fetch_gbif_data(api_url):
    """
    Fetch data from GBIF API and handle errors by returning a dictionary with 'error' if any.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raises HTTPError if status != 200
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}


def assign_survey_to_record(collection_record, owner_user):
    """
    Ensure the BiologicalCollectionRecord has a Survey whose date equals
    collection_record.collection_date. If the record already has a survey
    but its date doesn't match, switch it to the correct Survey.

    This fixes the bug where the survey date could differ from the record date.
    """
    if not collection_record.collection_date:
        # If there's no date, we can't reliably link to a dated survey.
        return

    # Attempt to get or create a matching survey
    try:
        survey, _ = Survey.objects.get_or_create(
            site=collection_record.site,
            date=collection_record.collection_date,
            collector_user=owner_user,
            owner=owner_user,
            defaults={'validated': True}
        )
    except Survey.MultipleObjectsReturned:
        # If multiple exist, use the first
        survey = Survey.objects.filter(
            site=collection_record.site,
            date=collection_record.collection_date,
            collector_user=owner_user,
            owner=owner_user
        ).first()
        survey.validated = True
        survey.save()

    # Assign the correct survey
    collection_record.survey = survey


def process_gbif_row(
    row,
    owner,
    source_reference,
    source_collection,
    harvest_session,
    taxon_group,
    log,
    habitat = None,
    origin = None
) -> Tuple[Optional["BiologicalCollectionRecord"], bool]:
    """Synchronise a GBIF occurrence with *BiologicalCollectionRecord*.

    :param row: Raw occurrence dictionary as returned by the GBIF JSON API
    :param owner: GBIF occurrence owner
    :param source_reference: GBIF occurrence source reference
    :param source_collection: GBIF occurrence source collection
    :param harvest_session: GBIF occurrence harvest session
    :param taxon_group: GBIF occurrence taxon group
    :param log: Callable accepting a single ``str`` for streaming progress
    :param harvest_session: Current `HarvestSession` or *None* when called ad‑hoc
    :param habitat: Optional supplementary information
    :param origin: Optional supplementary information

    :return: tuple
        ``(record_or_none, processed)`` where ``record_or_none`` is a new
        unsaved :class:`BiologicalCollectionRecord` or *None* when an
        existing record was updated; and ``processed`` is a boolean flag
        indicating whether the row contributed to the harvest totals.
    """
    # Prevent pulling FBIS data back down from GBIF
    if row.get('projectId', '').lower() == 'fbis':
        log('FBIS data, skipping...')
        return None, False

    # Check harvest session canceled?
    if harvest_session:
        session = HarvestSession.objects.get(id=harvest_session.id)
        if session.canceled:
            # Reconnect the post_save signal before returning
            models.signals.post_save.connect(
                collection_post_save_handler,
                sender=BiologicalCollectionRecord
            )
            log('Harvest session canceled')
            return None, False

    # Filter out unwanted basis of record
    basis_of_record = row.get('basisOfRecord', '')
    if basis_of_record not in ACCEPTED_BASIS_OF_RECORD:
        log(f"Unsupported basisOfRecord '{basis_of_record}', skipping.")
        return None, False

    # Extract fields
    upstream_id = row.get(UPSTREAM_ID_KEY)
    longitude = float(row.get(LON_KEY))
    latitude = float(row.get(LAT_KEY))
    coord_uncertainty = row.get(COORDINATE_UNCERTAINTY_KEY).strip()
    coord_uncertainty = float(coord_uncertainty) if coord_uncertainty else 0
    event_date = row.get(EVENT_DATE_KEY, '')
    collector = row.get(COLLECTOR_KEY, '')
    institution_code = row.get(INSTITUTION_CODE_KEY, source_collection)
    reference = row.get(REFERENCE_KEY, '')
    species = row.get(SPECIES_KEY, None)
    dataset_key = row.get(DATASET_KEY, None)
    taxon_key = row.get(TAXON_KEY, None)
    accepted_taxon_key = row.get(ACCEPTED_TAXON_KEY, None)

    taxonomy = None

    if taxon_key:
        taxonomy = Taxonomy.objects.filter(gbif_key=taxon_key).first()

    if not taxonomy:
        if accepted_taxon_key and accepted_taxon_key != taxon_key:
            log(
                f"Skipping occurrence {upstream_id}: local taxonomy missing for GBIF taxonKey={taxon_key}. "
                f"GBIF marks it as a synonym of acceptedTaxonKey={accepted_taxon_key}. "
                f"Please import/sync this taxonomy before harvesting."
            )
        else:
            log(
                f"Skipping occurrence {upstream_id}: local taxonomy not found for GBIF taxonKey={taxon_key}."
            )
        return None, False

    # Attempt to parse event_date -> collection_date
    collection_date = None
    if event_date:
        s = str(event_date).strip()

        if "/" in s:
            log(f"Interval eventDate '{s}' for upstream_id={upstream_id}; skipping.")
            return None, False

        try:
            collection_date = parse(s)
        except Exception as e:
            log(f"Date parsing failed for event_date={s}: {e}")
            return None, False

    if not collection_date:
        log(
            f'Date not found for {upstream_id}, skipping.'
        )
        return None, False

    # Attempt to create or fetch GBIF dataset
    if dataset_key:
        dataset_qs = Dataset.objects.filter(uuid=dataset_key)
        if not dataset_qs.exists():
            create_dataset_from_gbif(dataset_key)

    # Build or find a location site
    site_point = Point(longitude, latitude, srid=4326)
    if coord_uncertainty > 0:
        location_sites = LocationSite.objects.filter(
            geometry_point__distance_lte=(site_point, D(m=coord_uncertainty))
        )
    else:
        location_sites = LocationSite.objects.filter(geometry_point__equals=site_point)

    if location_sites.exists():
        location_site = location_sites[0]
    else:
        # Create new site
        locality = row.get(LOCALITY_KEY) or \
                   row.get(VERBATIM_LOCALITY_KEY, DEFAULT_LOCALITY)

        location_type, _ = LocationType.objects.get_or_create(
            name='PointObservation',
            allowed_geometry='POINT'
        )
        location_site = LocationSite.objects.create(
            geometry_point=site_point,
            name=locality[:200],
            location_type=location_type,
            site_description=locality[:300]
        )

        if not location_site.site_code:
            site_code, _ = generate_site_code(
                location_site,
                lat=location_site.latitude,
                lon=location_site.longitude
            )
            location_site.site_code = site_code
            location_site.save()

    # Additional data
    additional_data = {
        'fetch_from_gbif': True,
        'date_fetched': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Check if a record with this upstream_id exists
    try:
        collection_record = BiologicalCollectionRecord.objects.get(upstream_id=upstream_id)
        # Update fields
        collection_record.site = location_site
        collection_record.taxonomy = taxonomy
        collection_record.source_reference = source_reference
        collection_record.original_species_name = species
        collection_record.collector = collector
        collection_record.source_collection = source_collection
        collection_record.institution_id = institution_code
        collection_record.reference = reference
        collection_record.module_group = taxon_group
        collection_record.additional_data = additional_data
        collection_record.collection_date = collection_date
        collection_record.owner = owner
        collection_record.validated = True

        if dataset_key:
            collection_record.dataset_key = dataset_key

        if habitat:
            collection_record.collection_habitat = habitat.lower()

        if origin:
            # Map origin string to internal category key
            for cat_code, cat_label in BiologicalCollectionRecord.CATEGORY_CHOICES:
                if origin.lower() == cat_label.lower():
                    origin = cat_code
                    break
            collection_record.category = origin

        assign_survey_to_record(collection_record, owner)

        collection_record.save()

        log(
            f'--- Updated existing record with upstream ID: {upstream_id}\n'
        )

        return None, True
    except BiologicalCollectionRecord.DoesNotExist:
        # Prepare a new record
        new_record = BiologicalCollectionRecord(
            upstream_id=upstream_id,
            site=location_site,
            taxonomy=taxonomy,
            source_collection=source_collection,
            source_reference=source_reference,
            collection_date=collection_date,
            owner=owner,
            original_species_name=species,
            collector=collector,
            institution_id=institution_code,
            reference=reference,
            module_group=taxon_group,
            validated=True,
            additional_data=additional_data,
            dataset_key=dataset_key or ''
        )

        if habitat:
            new_record.collection_habitat = habitat.lower()

        if origin:
            for cat_code, cat_label in BiologicalCollectionRecord.CATEGORY_CHOICES:
                if origin.lower() == cat_label.lower():
                    origin = cat_code
                    break
            new_record.category = origin

        # Assign a Survey to the new record (before bulk_create)
        assign_survey_to_record(new_record, owner)

        log(
            f'--- Prepared new record with upstream ID: {upstream_id}\n'
        )

        return new_record, True
    except BiologicalCollectionRecord.MultipleObjectsReturned:
        # If duplicates exist for the same upstream_id, keep the last and delete the others
        duplicates = BiologicalCollectionRecord.objects.filter(upstream_id=upstream_id)
        last_record = duplicates.last()
        duplicates.exclude(id=last_record.id).delete()

        log(
            f'--- Resolved duplicate records for upstream ID: {upstream_id}\n'
        )
        return None, True


def process_gbif_response(
    zip_path: Path,
    session_id: Optional[int],
    taxon_group: str,
    habitat: Optional[str] = None,
    origin: Optional[str] = None,
    log_file: Optional[str] = None,
    *,
    batch_size: int = 1000,
) -> Tuple[Optional[str], int]:
    """Import a Darwin‑Core archive downloaded from GBIF.

    :param zip_path: Filesystem path to the ``.zip`` file returned by the GBIF export
    :param session_id: Primary‑key of the active HarvestSession
    :param taxon_group: Context/metadata passed straight through to process_gbif_row
    :param habitat: Context/metadata passed straight through to process_gbif_row
    :param origin: Context/metadata passed straight through to process_gbif_row
    :param log_file: Optional path to a file where human‑readable progress messages
    :param batch_size: Number of new records to accumulate before issuing a
        ``bulk_create`` – tune to balance memory vs. database round‑trips.

    :return ``(error_msg_or_None, processed_count)``. If an unrecoverable
        error occurs while opening the archive the function returns a
        descriptive string and ``0``; otherwise *None* and the number of
        processed (ie. accepted) occurrences.
    """

    def _log(message: str) -> None:
        """Internal logging helper – writes to *log_file* or logger."""
        log_to_file_or_logger(log_file, message)

    try:
        with zipfile.ZipFile(zip_path) as zf:
            with zf.open("occurrence.txt") as occ_file:
                txt_io = io.TextIOWrapper(occ_file, encoding="utf-8")
                header = txt_io.readline().rstrip("\n\r").split("\t")
                reader = csv.DictReader(txt_io, fieldnames=header, delimiter="\t")

                gbif_owner, _ = Profile.objects.get_or_create(
                    username="GBIF", defaults={"first_name": "GBIF.org"}
                )
                database_record, _ = DatabaseRecord.objects.get_or_create(
                    name="Global Biodiversity Information Facility (GBIF)"
                )
                source_reference, _ = SourceReferenceDatabase.objects.get_or_create(
                    source_name="Global Biodiversity Information Facility (GBIF)",
                    defaults={"source": database_record},
                )
                source_collection = "gbif"

                harvest_session = None
                if session_id is not None:
                    try:
                        harvest_session = HarvestSession.objects.get(id=session_id)
                    except HarvestSession.DoesNotExist:
                        _log(f"HarvestSession id={session_id} not found – proceeding without session.")

                records_to_create: List["BiologicalCollectionRecord"] = []
                processed_count = 0

                for idx, row in enumerate(reader, start=1):
                    new_record, accepted = process_gbif_row(
                        row=row,
                        owner=gbif_owner,
                        source_reference=source_reference,
                        source_collection=source_collection,
                        harvest_session=harvest_session,
                        taxon_group=taxon_group,
                        log=_log,
                        habitat=habitat,
                        origin=origin,
                    )

                    if accepted:
                        processed_count += 1

                    if new_record is not None:
                        records_to_create.append(new_record)
                        if len(records_to_create) >= batch_size:
                            BiologicalCollectionRecord.objects.bulk_create(records_to_create)
                            records_to_create.clear()
                            _log(f"-- committed batch up to row {idx} (total={processed_count})")

                if records_to_create:
                    BiologicalCollectionRecord.objects.bulk_create(records_to_create)
                    records_to_create.clear()

                _log(f"-- processed {processed_count} accepted occurrences from archive")
                return None, processed_count

    except Exception as exc:
        return f"Could not read {zip_path}: {exc}", 0


def import_gbif_occurrences(
        taxonomy_ids=[],
        habitat=None,
        origin='',
        log_file_path=None,
        session_id=None,
        taxon_group=None,
        area_index=1,
):
    """
    Import GBIF occurrences based on a taxonomy GBIF key, iterating over offsets
    until all data is fetched. Handles optional boundary polygons or country codes.
    """

    base_country_codes = preferences.SiteSetting.base_country_code.split(',')
    site_boundary = preferences.SiteSetting.site_boundary
    extracted_polygons = []
    area = area_index

    if log_file_path:
        setup_logger(log_file_path)

    gbif_user = preferences.SiteSetting.gbif_username
    gbif_pass = preferences.SiteSetting.gbif_password

    auth = (gbif_user, gbif_pass)

    log = lambda m: log_to_file_or_logger(log_file_path, m)

    harvest_session = HarvestSession.objects.get(
        id=session_id
    )

    def fetch_and_process_gbif_data(country_codes, geom_str=''):
        """
        Helper function to fetch from the GBIF API in a loop until results are exhausted.
        """

        predicates = {
            "type": "and",
            "predicates": [
                {"type": "in", "key": "TAXON_KEY", "values": taxonomy_ids},
                {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
                {"type": "equals", "key": "HAS_GEOSPATIAL_ISSUE", "value": "false"},
                {"type": "in", "key": "BASIS_OF_RECORD", "values": ACCEPTED_BASIS_OF_RECORD},
                {"type": "equals", "key": "OCCURRENCE_STATUS", "value": "PRESENT"},
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

        if geom_str:
            predicates['predicates'].append(
                {
                    "type": "within",
                    "geometry": geom_str
                }
            )
        else:
            predicates['predicates'].append(
                {
                    "type": "in",
                    "key": "COUNTRY",
                    "values": country_codes
                }
            )

        log(predicates)

        key, status_code = submit_download(
            gbif_user,
            gbif_pass,
            predicate=predicates,
            description=f"Harvesting occurrences for multiple taxa",
            log=log,
        )

        max_retries = 10
        retry_wait_seconds = 5 * 60
        attempt = 0

        while (not key) and status_code == 429 and attempt < max_retries:
            attempt += 1
            log(f"GBIF rate-limited (429). Retrying in 5 minutes... attempt {attempt}/{max_retries}")

            check_interval = 5
            waited = 0
            while waited < retry_wait_seconds:
                if is_canceled(harvest_session):
                    log("Harvest canceled during backoff wait.")
                    return "Canceled"
                time.sleep(check_interval)
                waited += check_interval

            key, status_code = submit_download(
                gbif_user,
                gbif_pass,
                predicate=predicates,
                description="Harvesting occurrences for multiple taxa",
                log=log,
            )

        if not key:
            return "Download request failed"

        zip_url = get_ready_download_url(
            key, auth, log, lambda: is_canceled(harvest_session))
        if not zip_url:
            return "Status check failed"

        zip_path = download_archive(zip_url, key, auth, log)
        if not zip_path:
            return "Failed to download archive"

        error, data_count = process_gbif_response(
            zip_path,
            session_id,
            taxon_group,
            habitat,
            origin,
            log_file_path
        )

        if error:
            log_to_file_or_logger(log_file_path, message=f'{error}\n', is_error=True)
            return error

        return True

    # Extract boundary geometry if set
    if site_boundary:
        try:
            boundary = Boundary.objects.get(id=site_boundary.id)
            geometry = boundary.geometry
            if not geometry:
                raise ValueError("No geometry found for the boundary.")

            if isinstance(geometry, MultiPolygon):
                for geom in geometry:
                    extracted_polygons.append(geom)
            else:
                # Single-polygon or other geometry
                extracted_polygons.append(geometry)
        except Exception as e:
            log_to_file_or_logger(
                log_file_path,
                message=f"Error fetching boundary: {e}",
                is_error=True
            )

    message = ''
    try:
        chunk_first_id = taxonomy_ids[0]
        chunk_last_id = taxonomy_ids[-1]
        chunk_first = Taxonomy.objects.filter(gbif_key=chunk_first_id).first()
        chunk_last = Taxonomy.objects.filter(gbif_key=chunk_last_id).first()

        log_to_file_or_logger(log_file_path, message=f'Fetching GBIF data for {chunk_first} ... {chunk_last}')

        if site_boundary and extracted_polygons:
            total = len(extracted_polygons)
            start_slice = extracted_polygons[area_index - 1:]

            for batch_no, poly_batch in enumerate(chunked(start_slice, BOUNDARY_BATCH_SIZE), start=1):
                if session_id and HarvestSession.objects.get(id=session_id).canceled:
                    return

                cleaned_parts = []
                for poly in poly_batch:
                    gj = json.loads(poly.geojson)
                    gj["coordinates"] = round_coordinates(gj["coordinates"])
                    g = GEOSGeometry(json.dumps(gj))
                    g = _clean_polygonal(g)
                    if g is None:
                        log_to_file_or_logger(log_file_path,
                                              message="Skipped an invalid polygon after cleaning")
                        continue
                    if g.geom_type == "MultiPolygon":
                        cleaned_parts.extend(list(g))
                    else:
                        cleaned_parts.extend(list(g))

                if not cleaned_parts:
                    log_to_file_or_logger(log_file_path,
                                          message="Skipped batch: no valid polygons after cleaning")
                    continue

                multi = _union_polys(cleaned_parts)
                if multi is None:
                    log_to_file_or_logger(
                        log_file_path,
                        message="Skipped batch: union produced no valid polygonal geometry")
                    continue

                multi = _clean_polygonal(multi)
                if multi is None:
                    log_to_file_or_logger(
                        log_file_path,
                        message="Skipped batch: final geometry invalid after cleaning")
                    continue

                multi = _enforce_ccw_exteriors(multi)

                multi = _clean_polygonal(multi)
                if multi is None:
                    log_to_file_or_logger(
                        log_file_path,
                        message="Skipped batch: invalid after orientation fix")
                    continue

                geometry_str = multi.wkt

                first_idx = (area_index - 1) + (batch_no - 1) * BOUNDARY_BATCH_SIZE + 1
                last_idx = min(first_idx + len(poly_batch) - 1, total)
                log_to_file_or_logger(
                    log_file_path,
                    message=(f'Areas batch {batch_no}: polygons {first_idx}-{last_idx} '
                             f'of {total} (batch size={len(poly_batch)})\n')
                )

                message = fetch_and_process_gbif_data(base_country_codes, geometry_str)
                log_to_file_or_logger(log_file_path, message=message)

        else:
            # No boundary: fetch all data by country codes only
            message = fetch_and_process_gbif_data(base_country_codes)

    except Exception as e:
        log_to_file_or_logger(log_file_path, message=str(e))
        return str(e)

    return message
