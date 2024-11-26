import json
from logging.handlers import RotatingFileHandler

import requests
import logging
import datetime
from django.contrib.gis.geos import MultiPolygon

from bims.models.source_reference import DatabaseRecord

from bims.models.location_site import generate_site_code
from dateutil.parser import parse, ParserError
from bims.models.survey import Survey
from preferences import preferences
from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.gis.db import models
from django.contrib.gis.measure import D

from bims.scripts.extract_dataset_keys import create_dataset_from_gbif
from geonode.people.models import Profile
from bims.models import (
    LocationSite,
    LocationType,
    BiologicalCollectionRecord,
    collection_post_save_handler,
    HarvestSession, SourceReferenceDatabase,
    Boundary,
    Dataset
)
from bims.utils.gbif import round_coordinates

logger = logging.getLogger('bims')

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
DEFAULT_LOCALITY = 'No locality, from GBIF'
SPECIES_KEY = 'species'
DATASET_KEY = 'datasetKey'
MODIFIED_DATE_KEY = 'modified'
LIMIT = 20

# Constants for better readability and maintainability
API_BASE_URL = 'http://api.gbif.org/v1/occurrence/search'
DEFAULT_LIMIT = 300
LOG_TEMPLATE = '---------------------------------------------------\nFetching: {}\n'
MISSING_KEY_ERROR = 'Missing taxon GBIF key'

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
    country_params = '&' + (
        '&'.join([f'country={code.upper()}' for code in base_country_codes.split(',')])
    )
    boundary_params = ''

    if boundary_str:
        boundary_params = f'&geometry={boundary_str}'
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


def setup_logger(log_file_path, max_bytes=10 ** 6, backup_count=10):
    """
    Set up the logger with a rotating file handler.
    """
    # Create a specific logger
    logger = logging.getLogger('harvest_logger')
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = RotatingFileHandler(log_file_path, maxBytes=max_bytes, backupCount=backup_count)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


def log_to_file_or_logger(log_file_path, message, is_error=False):
    """
    Log messages to either a file or the logger.
    """
    logger = logging.getLogger('harvest_logger')
    if not logger.handlers and log_file_path:
        setup_logger(log_file_path)
    if is_error:
        logger.error(message)
    else:
        logger.info(message)


def fetch_gbif_data(api_url):
    """
    Fetch data from GBIF API and handle errors.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        return {'error': error_message}


def process_gbif_response(json_result,
                          session_id,
                          taxon_group,
                          taxonomy,
                          habitat,
                          origin,
                          log_file=None):
    """
    Process GBIF API response using batch insertion.
    """

    if 'error' in json_result:
        log_to_file_or_logger(log_file, json_result['error'], is_error=True)
        return json_result['error'], 0

    source_collection = 'gbif'
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

    # List to hold records for bulk insertion
    records_to_create = []
    batch_size = 1000  # You can adjust the batch size based on your memory constraints

    for index, result in enumerate(json_result['results'], start=1):
        # Prevent pulling FBIS data back down from GBIF
        if 'projectId' in result and result['projectId'].lower() == 'fbis':
            continue

        basis_of_record = result.get('basisOfRecord', '')
        if basis_of_record not in ACCEPTED_BASIS_OF_RECORD:
            log_to_file_or_logger(
                log_file,
                f'Basis of record {basis_of_record} is not in the accepted list')
            continue

        if session_id:
            if HarvestSession.objects.get(id=session_id).canceled:
                log_to_file_or_logger(
                    log_file,
                    'Cancelled'
                )
                models.signals.post_save.connect(
                    collection_post_save_handler,
                    sender=BiologicalCollectionRecord
                )
                return 'Harvest session canceled', 0

        upstream_id = result.get(UPSTREAM_ID_KEY, None)
        longitude = result.get(LON_KEY)
        latitude = result.get(LAT_KEY)
        coordinate_uncertainty = result.get(COORDINATE_UNCERTAINTY_KEY, 0)
        event_date = result.get(EVENT_DATE_KEY,
                                result.get(MODIFIED_DATE_KEY, None))
        collector = result.get(COLLECTOR_KEY, '')
        institution_code = result.get(INSTITUTION_CODE_KEY, source_collection)
        reference = result.get(REFERENCE_KEY, '')
        species = result.get(SPECIES_KEY, None)
        collection_date = None
        dataset_key = result.get(DATASET_KEY, None)

        if dataset_key:
            datasets = Dataset.objects.filter(uuid=dataset_key)
            if not datasets.exists():
                dataset, created = create_dataset_from_gbif(dataset_key)

        if event_date:
            try:
                collection_date = parse(event_date)
            except ParserError:
                logger.error('Date is not in the correct format')
                continue

        site_point = Point(longitude, latitude, srid=4326)

        # Check nearest site based on site point and coordinate uncertainty
        if coordinate_uncertainty > 0:
            location_sites = LocationSite.objects.filter(
                geometry_point__distance_lte=(
                    site_point,
                    D(m=coordinate_uncertainty))
            )
        else:
            location_sites = LocationSite.objects.filter(
                geometry_point__equals=site_point
            )

        if location_sites.exists():
            # Get first site
            location_site = location_sites[0]
        else:
            # Create a new site
            locality = result.get(LOCALITY_KEY, result.get(
                VERBATIM_LOCALITY_KEY, DEFAULT_LOCALITY
            ))

            location_type, status = LocationType.objects.get_or_create(
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
                site_code, catchments_data = generate_site_code(
                    location_site,
                    lat=location_site.latitude,
                    lon=location_site.longitude
                )
                location_site.site_code = site_code
                location_site.save()

        # Prepare additional data
        additional_data = result
        additional_data['fetch_from_gbif'] = True
        additional_data['date_fetched'] = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'
        )

        # Create or update existing record
        try:
            collection_record = BiologicalCollectionRecord.objects.get(
                upstream_id=upstream_id
            )
            # Update existing record fields
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
                for category in BiologicalCollectionRecord.CATEGORY_CHOICES:
                    if origin.lower() == category[1].lower():
                        origin = category[0]
                        break
                collection_record.category = origin

            if not collection_record.survey and collection_record.collection_date:
                try:
                    survey, _ = Survey.objects.get_or_create(
                        site=collection_record.site,
                        date=collection_record.collection_date,
                        collector_user=collection_record.collector_user,
                        owner=collection_record.owner
                    )
                except Survey.MultipleObjectsReturned:
                    survey = Survey.objects.filter(
                        site=collection_record.site,
                        date=collection_record.collection_date,
                        collector_user=collection_record.collector_user,
                        owner=collection_record.owner
                    )[0]
                collection_record.survey = survey

            collection_record.save()

            log_to_file_or_logger(
                log_file,
                f'--- Updated existing collection record with upstream ID: {upstream_id}\n'
            )

        except BiologicalCollectionRecord.DoesNotExist:
            # Prepare a new record for bulk creation
            collection_record = BiologicalCollectionRecord(
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
                collection_record.collection_habitat = habitat.lower()
            if origin:
                for category in BiologicalCollectionRecord.CATEGORY_CHOICES:
                    if origin.lower() == category[1].lower():
                        origin = category[0]
                        break
                collection_record.category = origin

            try:
                survey, _ = Survey.objects.get_or_create(
                    site=location_site,
                    date=collection_date,
                    collector_user=gbif_owner,
                    owner=gbif_owner,
                    defaults={
                        'validated': True
                    }
                )
            except Survey.MultipleObjectsReturned:
                survey = Survey.objects.filter(
                    site=location_site,
                    date=collection_date,
                    collector_user=gbif_owner,
                    owner=gbif_owner
                )[0]
                survey.validated = True
                survey.save()
            collection_record.survey = survey

            records_to_create.append(collection_record)

            log_to_file_or_logger(
                log_file,
                f'--- Prepared new collection record with upstream ID: {upstream_id}\n'
            )

        except BiologicalCollectionRecord.MultipleObjectsReturned:
            collection_records = BiologicalCollectionRecord.objects.filter(
                upstream_id=upstream_id
            )
            collection_record = collection_records.last()
            collection_records.exclude(id=collection_record.id).delete()
            log_to_file_or_logger(
                log_file,
                f'--- Resolved duplicate records for upstream ID: {upstream_id}\n'
            )

        # Bulk create records when batch size is reached
        if len(records_to_create) >= batch_size:
            BiologicalCollectionRecord.objects.bulk_create(records_to_create)
            records_to_create.clear()

    # Insert any remaining records
    if records_to_create:
        BiologicalCollectionRecord.objects.bulk_create(records_to_create)
        records_to_create.clear()

    log_to_file_or_logger(log_file,
                          f"-- Processed {len(json_result['results'])} occurrences\n")
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
        area_index=1):
    """
    Import GBIF occurrences based on taxonomy GBIF key, without using recursion.
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

    def fetch_and_process_gbif_data(
            data_offset,
            country_codes,
            geom_str=''
    ):
        while True:
            api_url = build_api_url(
                taxonomy.gbif_key, data_offset,
                country_codes, geom_str)
            log_to_file_or_logger(
                log_file_path,
                f'URL: {api_url}\n'
            )

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
                log_to_file_or_logger(
                    log_file_path,
                    message=f'{error}\n',
                    is_error=True
                )
                break
            if data_count <= (data_offset + DEFAULT_LIMIT):
                break
            data_offset += DEFAULT_LIMIT
        return 'Finish'

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
                extracted_polygons.append(geometry)
        except Exception as e:
            log_to_file_or_logger(
                log_file_path,
                message=f"Error fetching boundary: {e}",
                is_error=True
            )

    message = ''
    try:
        log_to_file_or_logger(
            log_file_path,
            LOG_TEMPLATE.format(taxonomy.canonical_name)
        )
        if site_boundary:
            for polygon in extracted_polygons[area_index-1:]:
                if HarvestSession.objects.get(id=session_id).canceled:
                    return
                geojson = json.loads(polygon.geojson)
                geojson['coordinates'] = round_coordinates(
                    geojson['coordinates'])
                geometry_rounded = GEOSGeometry(json.dumps(geojson))
                geometry_str = str(geometry_rounded.ogr)
                log_to_file_or_logger(
                    log_file_path,
                    message='Area=({area}/{total_area})\n'.format(
                        area=area,
                        total_area=len(extracted_polygons))
                )
                area += 1
                message = fetch_and_process_gbif_data(offset, base_country_codes, geometry_str)
                log_to_file_or_logger(
                    log_file_path,
                    message=message)
        else:
            message = fetch_and_process_gbif_data(offset, base_country_codes)
    except Exception as e:  # noqa
        log_to_file_or_logger(
              log_file_path,
              message=str(e)
          )
        return str(e)
    return message
