import requests
import logging
import datetime
from dateutil.parser import parse
from requests.exceptions import HTTPError
from django.contrib.gis.geos import Point
from django.conf import settings
from django.contrib.gis.measure import D
from geonode.people.models import Profile
from bims.models import (
    LocationSite,
    LocationType,
    BiologicalCollectionRecord
)

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


def import_gbif_occurrences(
    taxonomy,
    offset=0,
    habitat=None,
    origin=None):
    """
    Import gbif occurrences based on taxonomy gbif key,
    data stored to biological_collection_record table
    :param taxonomy: Taxonomy object
    :param offset: response data offset, default is 0
    :param habitat: habitat of species, default to None
    :param origin: origin of species, default to None
    """
    api_url = 'http://api.gbif.org/v1/occurrence/search?'
    api_url += 'taxonKey={}'.format(taxonomy.gbif_key)
    api_url += '&offset={}'.format(offset)
    # We need data with coordinate
    api_url += '&hasCoordinate=true'
    # We don't need data with geospatial issue
    api_url += '&hasGeospatialIssue=false'

    try:
        response = requests.get(api_url)
        json_result = response.json()
        data_count = json_result['count']
    except HTTPError as e:
        logger.error(e.message)
        return

    source_collection = 'gbif'

    admins = settings.ADMINS
    superusers = Profile.objects.filter(is_superuser=True)
    if admins:
        for admin in admins:
            superuser_list = superusers.filter(email=admin[1])
            if superuser_list.exists():
                superusers = superuser_list
                break
    if superusers.exists():
        user = superusers[0]
    else:
        user = None

    for result in json_result['results']:
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
            location_type, status = LocationType.objects.get_or_create(
                name='PointObservation',
                allowed_geometry='POINT'
            )
            location_site = LocationSite.objects.create(
                geometry_point=site_point,
                name=locality,
                location_type=location_type
            )

        try:
            collection_record = BiologicalCollectionRecord.objects.get(
                upstream_id=upstream_id
            )
            logger.info(
                'Update existing collection record with upstream ID : {}'.
                format(upstream_id))
        except BiologicalCollectionRecord.DoesNotExist:
            logger.info(
                'Collection record created with upstream ID : {}'.
                format(upstream_id))
            collection_record = BiologicalCollectionRecord.objects.create(
                upstream_id=upstream_id,
                site=location_site,
                taxonomy=taxonomy
            )
        if event_date:
            collection_record.collection_date = parse(event_date)
        else:
            pass
        collection_record.taxonomy = taxonomy
        collection_record.owner = user
        collection_record.original_species_name = species
        collection_record.collector = collector
        collection_record.source_collection = source_collection
        collection_record.institution_id = institution_code
        collection_record.reference = reference
        collection_record.collection_habitat = habitat.lower()

        for category in BiologicalCollectionRecord.CATEGORY_CHOICES:
            if origin.lower() == category[1].lower():
                origin = category[0]
                break

        collection_record.category = origin
        collection_record.validated = True
        collection_record.additional_data = {
            'fetch_from_gbif': True,
            'date_fetched': datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'
            )
        }
        collection_record.save()

        logger.info('Collection record id {} has been updated'.format(
            collection_record.id
        ))

    if data_count > offset:
        # Import more occurrences
        import_gbif_occurrences(
            taxonomy=taxonomy,
            offset=offset + 20,
            habitat=habitat,
            origin=origin,
        )
