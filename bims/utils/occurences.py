from urllib.error import HTTPError
import logging

import requests
import simplejson
from django.conf import settings
from preferences import preferences


logger = logging.getLogger(__name__)

GBIF_API = getattr(settings, 'GBIF_API_BASE_URL', 'https://api.gbif.org/v1')


def get_fields_from_occurrences(record):

    api_url = GBIF_API + '/occurrence/{}'.format(record.upstream_id)

    try:
        response = requests.get(api_url)
        json_result = response.json()
        return json_result

    except (HTTPError, KeyError, simplejson.errors.JSONDecodeError) as e:
        print(e)
        return None









