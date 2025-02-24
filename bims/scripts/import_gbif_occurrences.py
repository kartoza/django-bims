import json
import datetime
import logging
from logging.handlers import RotatingFileHandler

import requests
from dateutil.parser import parse, ParserError
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, MultiPolygon, GEOSGeometry
from django.contrib.gis.measure import D

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


def build_api_url(taxonomy_gbif_key, offset, base_country_codes, boundary_str=''):
    """
    Construct the API URL with query parameters.
    """
    country_params = ''
    if base_country_codes:
        country_list = [code.strip().upper() for code in base_country_codes.split(',')]
        # e.g. &country=ZA&country=BW
        country_params = '&' + '&'.join(f'country={code}' for code in country_list)

    boundary_params = ''
    if boundary_str:
        boundary_params = f'&geometry={boundary_str}'
        # If geometry is provided, skip country params
        country_params = ''

    return (
        f"{API_BASE_URL}?"
        f"taxonKey={taxonomy_gbif_key}&"
        f"offset={offset}&"
        f"hasCoordinate=true&"
        f"hasGeospatialIssue=false&"
        f"limit={DEFAULT_LIMIT}"
        f"{country_params}"
        f"{boundary_params}"
    )


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


def process_gbif_response(
        json_result,
        session_id,
        taxon_group,
        taxonomy,
        habitat,
        origin,
        log_file=None
):
    """
    Process the GBIF API response by inserting/updating BiologicalCollectionRecord
    objects in batches. Returns (error_message, total_processed_count).
    """
    if 'error' in json_result:
        log_to_file_or_logger(log_file, json_result['error'], is_error=True)
        return json_result['error'], 0

    gbif_owner, _ = Profile.objects.get_or_create(
        username='GBIF',
        first_name='GBIF.org'
    )

    database_record, _ = DatabaseRecord.objects.get_or_create(
        name='Global Biodiversity Information Facility (GBIF)'
    )
    source_reference, _ = SourceReferenceDatabase.objects.get_or_create(
        source_name='Global Biodiversity Information Facility (GBIF)',
        source=database_record
    )

    # Prepare for bulk creation
    records_to_create = []
    batch_size = 1000  # Adjust as needed
    source_collection = 'gbif'

    for index, result in enumerate(json_result['results'], start=1):
        # Prevent pulling FBIS data back down from GBIF
        if result.get('projectId', '').lower() == 'fbis':
            continue

        # Check harvest session canceled?
        if session_id:
            session = HarvestSession.objects.get(id=session_id)
            if session.canceled:
                log_to_file_or_logger(log_file, 'Cancelled')
                # Reconnect the post_save signal before returning
                models.signals.post_save.connect(
                    collection_post_save_handler,
                    sender=BiologicalCollectionRecord
                )
                return 'Harvest session canceled', 0

        # Filter out unwanted basis of record
        basis_of_record = result.get('basisOfRecord', '')
        if basis_of_record not in ACCEPTED_BASIS_OF_RECORD:
            log_to_file_or_logger(
                log_file,
                f'Basis of record {basis_of_record} not accepted.'
            )
            continue

        # Extract fields
        upstream_id = result.get(UPSTREAM_ID_KEY)
        longitude = result.get(LON_KEY)
        latitude = result.get(LAT_KEY)
        coord_uncertainty = result.get(COORDINATE_UNCERTAINTY_KEY, 0)
        event_date = result.get(EVENT_DATE_KEY) or result.get(MODIFIED_DATE_KEY)
        collector = result.get(COLLECTOR_KEY, '')
        institution_code = result.get(INSTITUTION_CODE_KEY, source_collection)
        reference = result.get(REFERENCE_KEY, '')
        species = result.get(SPECIES_KEY, None)
        dataset_key = result.get(DATASET_KEY, None)

        # Attempt to parse event_date -> collection_date
        collection_date = None
        if event_date:
            try:
                collection_date = parse(event_date)
            except ParserError:
                logger.error('Date parsing failed for event_date=%s', event_date)
                continue

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
            locality = result.get(LOCALITY_KEY) or \
                       result.get(VERBATIM_LOCALITY_KEY, DEFAULT_LOCALITY)

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
        additional_data = dict(result)
        additional_data['fetch_from_gbif'] = True
        additional_data['date_fetched'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
            collection_record.owner = gbif_owner
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

            assign_survey_to_record(collection_record, gbif_owner)

            collection_record.save()

            log_to_file_or_logger(
                log_file,
                f'--- Updated existing record with upstream ID: {upstream_id}\n'
            )

        except BiologicalCollectionRecord.DoesNotExist:
            # Prepare a new record
            new_record = BiologicalCollectionRecord(
                upstream_id=upstream_id,
                site=location_site,
                taxonomy=taxonomy,
                source_collection=source_collection,
                source_reference=source_reference,
                collection_date=collection_date,
                owner=gbif_owner,
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
            assign_survey_to_record(new_record, gbif_owner)

            # Collect for bulk creation
            records_to_create.append(new_record)

            log_to_file_or_logger(
                log_file,
                f'--- Prepared new record with upstream ID: {upstream_id}\n'
            )

        except BiologicalCollectionRecord.MultipleObjectsReturned:
            # If duplicates exist for the same upstream_id, keep the last and delete the others
            duplicates = BiologicalCollectionRecord.objects.filter(upstream_id=upstream_id)
            last_record = duplicates.last()
            duplicates.exclude(id=last_record.id).delete()

            log_to_file_or_logger(
                log_file,
                f'--- Resolved duplicate records for upstream ID: {upstream_id}\n'
            )

        # Bulk create if we exceed the batch size
        if len(records_to_create) >= batch_size:
            BiologicalCollectionRecord.objects.bulk_create(records_to_create)
            records_to_create.clear()

    # Create any remaining records
    if records_to_create:
        BiologicalCollectionRecord.objects.bulk_create(records_to_create)
        records_to_create.clear()

    total = len(json_result.get('results', []))
    log_to_file_or_logger(log_file, f"-- Processed {total} occurrences\n")
    return None, json_result['count']


def import_gbif_occurrences(
        taxonomy,
        offset=0,
        owner=None,
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

    base_country_codes = preferences.SiteSetting.base_country_code
    site_boundary = preferences.SiteSetting.site_boundary
    extracted_polygons = []
    area = area_index

    if log_file_path:
        setup_logger(log_file_path)

    def fetch_and_process_gbif_data(data_offset, country_codes, geom_str=''):
        """
        Helper function to fetch from the GBIF API in a loop until results are exhausted.
        """
        while True:
            api_url = build_api_url(taxonomy.gbif_key, data_offset, country_codes, geom_str)
            log_to_file_or_logger(log_file_path, f'URL: {api_url}\n')

            json_result = fetch_gbif_data(api_url)
            if 'error' in json_result:
                log_to_file_or_logger(
                    log_file_path,
                    message=f"{json_result['error']}\n",
                    is_error=True
                )
                return json_result['error']

            error, data_count = process_gbif_response(
                json_result,
                session_id,
                taxon_group,
                taxonomy,
                habitat,
                origin,
                log_file_path
            )
            if error:
                log_to_file_or_logger(log_file_path, message=f'{error}\n', is_error=True)
                break

            # If we've fetched all results, break
            if data_count <= (data_offset + DEFAULT_LIMIT):
                break

            data_offset += DEFAULT_LIMIT
        return 'Finish'

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
                    offset,
                    base_country_codes,
                    geometry_str
                )
                log_to_file_or_logger(log_file_path, message=message)

        else:
            # No boundary: fetch all data by country codes only
            message = fetch_and_process_gbif_data(offset, base_country_codes)

    except Exception as e:
        log_to_file_or_logger(log_file_path, message=str(e))
        return str(e)

    return message
