# coding: utf-8
import requests
import simplejson
from requests.exceptions import HTTPError

CITES_TOKEN = "lrPUQ0QDKDwwXkAIIM18cgtt"
CITES_API_URL = "https://api.speciesplus.net/api/v1/taxon_concepts/"


def get_cites_status(taxon_id):
    """
    Get cites status by taxon id
    :param taxon_id: gbif id
    :return: cites status of a taxon
    """

    headers = {
        'X-Authentication-Token': CITES_TOKEN,
    }
    cites_legislation = "{}/cites_legislation".format(taxon_id)
    try:
        response = requests.get(CITES_API_URL+cites_legislation, headers=headers)
        json_result = response.json()
        return json_result
    except (HTTPError, KeyError, simplejson.errors.JSONDecodeError) as e:
        print(e)
        return None
