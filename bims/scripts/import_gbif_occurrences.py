import requests
import logging
from requests.exceptions import HTTPError
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from bims.models import LocationSite, LocationType, BiologicalCollectionRecord

logger = logging.getLogger('bims')

UPSTREAM_ID_KEY = 'gbifId'
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


def import_gbif_occurrences(taxonomy):
    """
    Import gbif occurrences based on taxonomy gbif key,
    data stored to biological_collection_record table
    :param taxonomy: Taxonomy object
    """
    api_url = 'http://api.gbif.org/v1/occurrence/search?'
    api_url += 'taxonKey={}'.format(taxonomy.gbif_key)

    try:
        response = requests.get(api_url)
        json_result = response.json()
    except HTTPError as e:
        logger.error(e.message)
        return

    source_collection = 'gbif'

    for result in json_result['results']:
        upstream_id = result.get(UPSTREAM_ID_KEY, None)
        longitude = result.get(LON_KEY)
        latitude = result.get(LAT_KEY)
        coordinate_uncertainty = result.get(COORDINATE_UNCERTAINTY_KEY, None)
        event_date = result.get(EVENT_DATE_KEY, None)
        collector = result.get(COLLECTOR_KEY, None)
        institution_code = result.get(INSTITUTION_CODE_KEY, None)
        reference = result.get(REFERENCE_KEY, None)
        species = result.get(SPECIES_KEY, None)

        site_point = GEOSGeometry('POINT({longitude} {latitude}'.format(
            longitude=longitude,
            latitude=latitude
        ), srid=4326)

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
        except BiologicalCollectionRecord.DoesNotExist:
            collection_record = BiologicalCollectionRecord.objects.create(
                upstream_id=upstream_id,
                site=location_site,
            )

        collection_record.collection_date = event_date
        collection_record.taxonomy = taxonomy
        collection_record.original_species_name = species
        collection_record.collector = collector
        collection_record.source_collection = source_collection
        collection_record.institution_id = institution_code
        collection_record.reference = reference
        collection_record.save()
