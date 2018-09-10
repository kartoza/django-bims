import requests
from requests.exceptions import HTTPError
from django.conf import settings
from bims.models.iucn_status import IUCNStatus
from bims.utils.get_key import get_key


def get_iucn_status(taxon_id=None, species_name=None):
    """
    Fetch iucn status of the species, and update the iucn record.

    :param taxon_id: taxon id of the species
    :param species_name: name of the species
    """
    api_iucn_key = get_key('IUCN_API_KEY')

    if not api_iucn_key:
        return None

    api_url = settings.IUCN_API_URL

    if taxon_id:
        api_url += '/id/' + taxon_id
    elif species_name:
        api_url += '/species/' + species_name
    else:
        return None

    # Add token
    api_url += '?token=' + api_iucn_key

    try:
        response = requests.get(api_url)
        json_result = response.json()
        if len(json_result['result']) > 0:
            iucn_status = IUCNStatus.objects.filter(
                category=json_result['result'][0]['category']
            )
            if not iucn_status:
                iucn_status = IUCNStatus.objects.create(
                    category=json_result['result'][0]['category']
                )
                return iucn_status
            return iucn_status[0]
        return None
    except (HTTPError, KeyError) as e:
        print(e)
        return None
