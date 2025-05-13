import logging

import requests
from requests.exceptions import HTTPError, SSLError

from bims.models.iucn_status import IUCNStatus
from preferences import preferences


logger = logging.getLogger(__name__)


def get_iucn_status(taxon):
    """
    Fetch IUCN status using genus/species name and return both
    IUCNStatus instance and sis_id (to set iucn_redlist_id manually).

    :param taxon: Taxonomy instance (must have genus_name and species_name)
    :return: tuple (IUCNStatus or None, sis_id or None, iucn_url or None)
    """
    api_iucn_key = preferences.SiteSetting.iucn_api_key

    if not api_iucn_key or not taxon.genus_name or not taxon.species_name:
        return None, None, None

    url = "https://api.iucnredlist.org/api/v4/taxa/scientific_name"
    headers = {
        'accept': 'application/json',
        'Authorization': api_iucn_key
    }

    species_name = taxon.species_name
    genus_name = taxon.genus_name

    if genus_name in species_name:
        species_name = species_name.replace(genus_name, '', 1).strip()

    params = {
        'genus_name': genus_name,
        'species_name': species_name
    }

    iucn_url = None

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        json_result = response.json()

        sis_id = json_result.get("taxon", {}).get("sis_id")

        assessments = json_result.get("assessments", [])
        latest = next((a for a in assessments if a.get("latest")), None)

        if latest:
            category = latest.get("red_list_category_code")
            iucn_url = latest.get("url")
            if category:
                try:
                    iucn_status, _ = IUCNStatus.objects.get_or_create(
                        category=category,
                        national=False
                    )
                except IUCNStatus.MultipleObjectsReturned:
                    iucn_status = IUCNStatus.objects.filter(
                        category=category,
                        national=False
                    ).first()
                return iucn_status, sis_id, iucn_url

        return None, sis_id, iucn_url

    except (HTTPError, SSLError,
            requests.exceptions.JSONDecodeError,
            requests.exceptions.RequestException) as e:
        logger.error(f"IUCN API error: {e}")
        return None, None, iucn_url
