import csv
import io
import json
import datetime
import logging
import os
import zipfile
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Tuple, Optional, List

import requests
from dateutil.parser import parse, ParserError
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
    Dataset
)
from bims.models.source_reference import DatabaseRecord
from bims.models.location_site import generate_site_code
from bims.models.survey import Survey
from bims.scripts.extract_dataset_keys import create_dataset_from_gbif
from bims.utils.gbif import round_coordinates


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
    'LIVING_SPECIMEN',
    'OBSERVATION',
    'HUMAN_OBSERVATION',
    'MACHINE_OBSERVATION',
    'MATERIAL_SAMPLE',
    'LITERATURE',
    'MATERIAL_CITATION',
    'OCCURRENCE'
]


def setup_logger(log_file_path, max_bytes=10**6, backup_count=10):
    """
    Set up and return a logger with a rotating file handler.
    """
    harvest_logger = logging.getLogger('harvest_logger')
    harvest_logger.setLevel(logging.INFO)

    # Clear any existing handlers to avoid duplicates
    if harvest_logger.hasHandlers():
        harvest_logger.handlers.clear()

    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
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
    taxonomy,
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
    :param taxonomy: GBIF occurrence taxonomy
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
    event_date = row.get(EVENT_DATE_KEY) or row.get(MODIFIED_DATE_KEY)
    collector = row.get(COLLECTOR_KEY, '')
    institution_code = row.get(INSTITUTION_CODE_KEY, source_collection)
    reference = row.get(REFERENCE_KEY, '')
    species = row.get(SPECIES_KEY, None)
    dataset_key = row.get(DATASET_KEY, None)

    # Attempt to parse event_date -> collection_date
    collection_date = None
    if event_date:
        try:
            collection_date = parse(event_date)
        except ParserError:
            log(
                f'Date parsing failed for event_date={event_date}'
            )
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
            additional_data=additional_data
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
    taxonomy,
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
    :param taxonomy: Context/metadata passed straight through to process_gbif_row
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
                        taxonomy=taxonomy,
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
        taxonomy,
        offset=0,
        habitat=None,
        origin='',
        log_file_path=None,
        session_id=None,
        taxon_group=None,
        area_index=1
):
    """
    Import GBIF occurrences based on a taxonomy GBIF key, iterating over offsets
    until all data is fetched. Handles optional boundary polygons or country codes.
    """
    if not taxonomy.gbif_key:
        logger.error(MISSING_KEY_ERROR)
        return MISSING_KEY_ERROR

    base_country_codes = preferences.SiteSetting.base_country_code.split(',')
    site_boundary = preferences.SiteSetting.site_boundary
    extracted_polygons = []
    area = area_index

    if log_file_path:
        setup_logger(log_file_path)

    gbif_user = os.environ.get("GBIF_USERNAME", "")
    gbif_pass = os.environ.get("GBIF_PASSWORD", "")

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
                {"type": "equals", "key": "TAXON_KEY", "value": str(taxonomy.gbif_key)},
                {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
                {"type": "equals", "key": "HAS_GEOSPATIAL_ISSUE", "value": "false"},
                {"type": "in", "key": "BASIS_OF_RECORD", "values": ACCEPTED_BASIS_OF_RECORD},
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

        key = submit_download(
            gbif_user,
            gbif_pass,
            predicate=predicates,
            description=f"Harvesting occurrences for taxon {taxonomy.scientific_name}",
            log=log,
        )

        if not key:
            return None

        zip_url = get_ready_download_url(
            key, auth, log, lambda: is_canceled(harvest_session))
        if not zip_url:
            return None

        zip_path = download_archive(zip_url, key, auth, log)
        if not zip_path:
            return None

        error, data_count = process_gbif_response(
            zip_path,
            session_id,
            taxon_group,
            taxonomy,
            habitat,
            origin,
            log_file_path
        )

        if error:
            log_to_file_or_logger(log_file_path, message=f'{error}\n', is_error=True)
            return None

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
        log_to_file_or_logger(log_file_path, LOG_TEMPLATE.format(taxonomy.canonical_name))

        # If a boundary is specified, loop each polygon area
        if site_boundary and extracted_polygons:
            for polygon in extracted_polygons[area_index - 1 :]:
                # Check if the harvest session was canceled
                if session_id and HarvestSession.objects.get(id=session_id).canceled:
                    return

                geojson = json.loads(polygon.geojson)
                geojson['coordinates'] = round_coordinates(geojson['coordinates'])
                geometry_rounded = GEOSGeometry(json.dumps(geojson))
                geometry_str = str(geometry_rounded.ogr)

                log_to_file_or_logger(
                    log_file_path,
                    message=f'Area=({area}/{len(extracted_polygons)})\n'
                )
                area += 1

                message = fetch_and_process_gbif_data(
                    base_country_codes,
                    geometry_str
                )
                log_to_file_or_logger(log_file_path, message=message)

        else:
            # No boundary: fetch all data by country codes only
            message = fetch_and_process_gbif_data(base_country_codes)

    except Exception as e:
        log_to_file_or_logger(log_file_path, message=str(e))
        return str(e)

    return message
