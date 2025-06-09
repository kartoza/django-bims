import logging
import requests
from requests.exceptions import HTTPError, SSLError

from bims.models.iucn_status import IUCNStatus
from preferences import preferences

logger = logging.getLogger(__name__)


def _make_iucn_request(endpoint: str, params: dict = None) -> dict | None:
    """
    Makes a GET request to the IUCN API.
    """
    api_key = preferences.SiteSetting.iucn_api_key
    if not api_key:
        return None

    url = f'https://api.iucnredlist.org/api/v4/{endpoint}'
    headers = {
        'accept': 'application/json',
        'Authorization': api_key
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, dict):
            if 'total-count' in response.headers:
                result['total_count'] = response.headers.get('total-count', 0)
            if 'total-pages' in response.headers:
                result['total_pages'] = response.headers.get('total-pages', 0)
            if 'current-page' in response.headers:
                result['current_page'] = response.headers.get('current-page', 0)
        return result
    except (HTTPError, SSLError,
            requests.exceptions.JSONDecodeError,
            requests.exceptions.RequestException) as e:
        logger.error(f"IUCN API error: {e}")
        return None


def get_assessment_detail(assessment_id: int) -> dict | None:
    """
    Retrieve IUCN assessment details for a given assessment ID.

    Args:
        assessment_id (int): The unique ID of the assessment.

    Returns:
        dict | None: A dictionary containing assessment details if successful,
        otherwise None if the request fails or the ID is invalid.
    """
    if not assessment_id:
        return None
    return _make_iucn_request(f'assessment/{assessment_id}')


def fetch_taxa(habitat_code: str, page: int = 1, per_page: int = 100) -> dict:
    """
    Retrieve a list of taxa associated with a specific habitat code.

    Also returns pagination metadata from response headers if present.

    Args:
        habitat_code (str): The IUCN habitat classification code.
        page (int): Page number to fetch.
        per_page (int): Number of items per page.

    Returns:
        dict: {
            "results": list of taxa records,
            "total_count": int,
            "total_pages": int,
            "current_page": int,
        }
    """
    if not habitat_code:
        return {
            "results": [],
            "total_count": 0,
            "total_pages": 0,
            "current_page": 0,
        }

    params = {"page": page, "per_page": per_page}
    result = _make_iucn_request(f'habitats/{habitat_code}', params=params)

    if result is None:
        return {
            "results": [],
            "total_count": 0,
            "total_pages": 0,
            "current_page": page,
        }

    return {
        "results": result.get('assessments', []),
        "total_count": int(result.get("total_count", 0)),
        "total_pages": int(result.get("total_pages", 0)),
        "current_page": int(result.get("current_page", page)),
    }


def get_iucn_status(taxon):
    """
    Fetch IUCN status using genus/species name and return both
    IUCNStatus instance and sis_id (to set iucn_redlist_id manually).

    :param taxon: Taxonomy instance (must have genus_name and species_name)
    :return: tuple (IUCNStatus or None, sis_id or None, iucn_url or None)
    """
    if not taxon.genus_name or not taxon.species_name:
        return None, None, None

    species_name = taxon.species_name
    genus_name = taxon.genus_name
    species_name = (
        taxon.species_name.replace(genus_name, '', 1).strip() if genus_name in species_name else species_name
    )

    params = {
        'genus_name': genus_name,
        'species_name': species_name
    }

    json_result = _make_iucn_request('taxa/scientific_name', params)
    if not json_result:
        return None, None, None

    sis_id = json_result.get("taxon", {}).get("sis_id")
    iucn_url = None

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
