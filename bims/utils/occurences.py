from urllib.error import HTTPError
import logging

import requests
import simplejson
from preferences import preferences


logger = logging.getLogger(__name__)


def get_fields_from_occurrences(record):

    api_url = 'http://api.gbif.org/v1/occurrence/{}'.format(record.upstream_id)

    try:
        response = requests.get(api_url)
        json_result = response.json()
        return json_result

    except (HTTPError, KeyError, simplejson.errors.JSONDecodeError) as e:
        print(e)
        return None









