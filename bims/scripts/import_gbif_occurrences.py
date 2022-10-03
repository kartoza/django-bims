import json

import requests
import logging
import datetime
import simplejson
from urllib3.exceptions import ProtocolError

from bims.models.source_reference import DatabaseRecord

from bims.models.location_site import generate_site_code
from dateutil.parser import parse
from requests.exceptions import HTTPError
from preferences import preferences
from django.contrib.gis.geos import Point
from django.contrib.gis.db import models
from django.contrib.gis.measure import D
from geonode.people.models import Profile
from bims.models import (
    LocationSite,
    LocationType,
    BiologicalCollectionRecord,
    collection_post_save_handler,
    HarvestSession, SourceReferenceDatabase
)
from bims.utils.get_key import get_key

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
MODIFIED_DATE_KEY = 'modified'
LIMIT = 20


def import_gbif_occurrences(
    taxonomy,
    offset=0,
    owner=None,
    habitat=None,
    origin='',
    log_file_path=None,
    session_id=None) -> str:
    """
    Import gbif occurrences based on taxonomy gbif key,
    data stored to biological_collection_record table
    :param taxonomy: Taxonomy object
    :param offset: response data offset, default is 0
    :param owner: owner of record in the bims
    :param habitat: habitat of species, default to None
    :param origin: origin of species, default to None
    :param log_file_path: Path of log file of the current process,
        if provided then write the log to this file
    :param session_id: Id of the harvest session
    """
    log_file = None
    if log_file_path:
        log_file = open(log_file_path, 'a')
        log_file.write('---------------------------------------------------\n')
        log_file.write('Fetching : {}\n'.format(taxonomy.canonical_name))

    if not taxonomy.gbif_key:
        if log_file:
            log_file.write('Missing taxon gbif key\n')
        else:
            logger.error('Missing taxon gbif key')
        return 'Missing taxon gbif key'
    api_url = 'http://api.gbif.org/v1/occurrence/search?'
    api_url += 'taxonKey={}'.format(taxonomy.gbif_key)
    api_url += '&offset={}'.format(offset)
    # We need data with coordinate to create a site
    api_url += '&hasCoordinate=true'
    # We don't need data with geospatial issue
    api_url += '&hasGeospatialIssue=false'
    # Only fetch from Specific country
    for country_code in preferences.SiteSetting.base_country_code.split(','):
        api_url += '&country={}'.format(country_code.upper())

    if log_file:
        log_file.write('URL : {}\n'.format(api_url))

    try:
        response = requests.get(api_url)
        json_result = response.json()
        data_count = json_result['count']
    except (
            HTTPError, simplejson.errors.JSONDecodeError,
            ProtocolError) as e:
        if hasattr(e, 'message'):
            error_message = e.message
        else:
            error_message = str(e)
        if log_file:
            log_file.write(error_message)
        else:
            logger.error(error_message)
        return error_message

    if log_file:
        log_file.write(
            '-- Total occurrences {total} - offset {offset} : \n'.format(
                offset=offset,
                total=data_count
            )
        )
    else:
        logger.info('-- Total occurrences {total} - offset {offset} : '.format(
            offset=offset,
            total=data_count
        ))

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


    for result in json_result['results']:
        if session_id:
            if HarvestSession.objects.get(id=session_id).canceled:
                if log_file:
                    log_file.write('Cancelled')
                else:
                    logger.info('Cancelled')
                if log_file:
                    log_file.close()

                # reconnect post save handler
                models.signals.post_save.connect(
                    collection_post_save_handler,
                    sender=BiologicalCollectionRecord
                )
                return 'Harvest session canceled'
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

        site_point = Point(longitude, latitude, srid=4326)

        # Check nearest site based on site point and coordinate uncertainty
        location_sites = LocationSite.objects.filter(
            geometry_point__distance_lte=(
                site_point,
                D(m=coordinate_uncertainty))
        )
        if location_sites.exists():
            # Get first site
            location_site = location_sites[0]
        else:
            # Create a new site
            locality = result.get(LOCALITY_KEY, result.get(
                VERBATIM_LOCALITY_KEY, DEFAULT_LOCALITY
            ))

            # Check if site is in the correct border
            boundary_key = preferences.SiteSetting.boundary_key
            if boundary_key:
                url = (
                    '{base_url}/api/v2/query?registry=service&key={key}&'
                    'x={lon}&y={lat}&outformat=json'
                ).format(
                    base_url=get_key('GEOCONTEXT_URL'),
                    key=boundary_key,
                    lon=longitude,
                    lat=latitude
                )
                try:
                    response = requests.get(url)
                    if response.status_code != 200:
                        log_file.write(
                            '{0},{1} :'
                            ' The site is not within a valid border,'
                            ' skip -- \n'.format(
                                longitude, latitude
                            )
                        )
                        logger.info(
                            f'The site is not within a valid border.'
                        )
                        continue
                    else:
                        response_json = json.loads(response.content)
                        if response_json['value']:
                            logger.info(
                                f"Site is in {response_json['value']}"
                            )
                        else:
                            logger.info(
                                f'The site is not within a valid border.'
                            )
                            log_file.write(
                                '{0},{1} :'
                                ' The site is not within a valid border,'
                                ' skip -- \n'.format(
                                    longitude, latitude
                                )
                            )
                            continue
                except Exception as e:  # noqa
                    logger.info(
                        f'Unable to check boundary data from geocontext')

            location_type, status = LocationType.objects.get_or_create(
                name='PointObservation',
                allowed_geometry='POINT'
            )
            location_site = LocationSite.objects.create(
                geometry_point=site_point,
                name=locality,
                location_type=location_type,
                site_description=locality
            )
            if not location_site.site_code:
                site_code, catchments_data = generate_site_code(
                    location_site,
                    lat=location_site.latitude,
                    lon=location_site.longitude
                )
                location_site.site_code = site_code
                location_site.save()

        try:
            collection_record = BiologicalCollectionRecord.objects.get(
                upstream_id=upstream_id
            )
            if log_file:
                log_file.write(
                    '--- Update existing '
                    'collection record with upstream ID : {}\n'.
                    format(upstream_id)
                )
            else:
                logger.info(
                    '--- Update existing collection record with'
                    ' upstream ID : {}'.
                    format(upstream_id))
        except BiologicalCollectionRecord.DoesNotExist:
            if log_file:
                log_file.write(
                    '--- Collection record created with upstream ID : {}\n'.
                    format(upstream_id)
                )
            else:
                logger.info(
                    '--- Collection record created with upstream ID : {}'.
                    format(upstream_id))
            collection_record = BiologicalCollectionRecord.objects.create(
                upstream_id=upstream_id,
                site=location_site,
                taxonomy=taxonomy,
                source_collection=source_collection,
                source_reference=source_reference
            )
        if event_date:
            collection_record.collection_date = parse(event_date)
        else:
            pass
        collection_record.taxonomy = taxonomy
        collection_record.owner = gbif_owner
        collection_record.original_species_name = species
        collection_record.collector = collector
        collection_record.source_collection = source_collection
        collection_record.institution_id = institution_code
        collection_record.reference = reference
        if habitat:
            collection_record.collection_habitat = habitat.lower()
        if origin:
            for category in BiologicalCollectionRecord.CATEGORY_CHOICES:
                if origin.lower() == category[1].lower():
                    origin = category[0]
                    break
            collection_record.category = origin
        collection_record.validated = True
        additional_data = result
        additional_data['fetch_from_gbif'] = True
        additional_data['date_fetched'] = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        collection_record.additional_data = additional_data
        collection_record.save()

    if log_file:
        log_file.close()

    if data_count > (offset + LIMIT):
        # Import more occurrences
        import_gbif_occurrences(
            taxonomy=taxonomy,
            offset=offset + LIMIT,
            habitat=habitat,
            origin=origin,
            log_file_path=log_file_path,
            session_id=session_id
        )

    return 'Finish'
