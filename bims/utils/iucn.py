import logging
import time

import requests
from requests.exceptions import HTTPError, SSLError

from bims.models.iucn_status import IUCNStatus
from preferences import preferences


logger = logging.getLogger(__name__)


class IUCNRateLimitError(Exception):
    """Raised when the IUCN API keeps returning HTTP 429 (Too Many Requests)."""


LEGACY_CATEGORY_MAP = {
    'V': 'VU',
}


def normalize_iucn_category_code(code):
    if not code:
        return None
    normalized = code.strip()
    return LEGACY_CATEGORY_MAP.get(normalized, normalized)


def fetch_iucn_data(taxon):
    """
    Fetch IUCN data using genus/species name and return the JSON payload.

    :param taxon: Taxonomy instance (must have genus_name and species_name)
    :return: dict or None
    """
    api_iucn_key = preferences.SiteSetting.iucn_api_key

    species_name = taxon.species_name
    taxon_name_list = species_name.split(' ')
    if not taxon.parent and species_name and len(taxon_name_list) > 1:
        genus_name = taxon_name_list[0].strip()
    else:
        genus_name = taxon.genus_name

    if genus_name and genus_name in species_name:
        species_name = species_name.replace(genus_name, '', 1).strip()

    if not api_iucn_key or not genus_name or not species_name:
        return None

    url = "https://api.iucnredlist.org/api/v4/taxa/scientific_name"
    headers = {
        'accept': 'application/json',
        'Authorization': api_iucn_key
    }

    params = {
        'genus_name': genus_name,
        'species_name': species_name
    }

    max_retries = 4
    backoff = 2
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                try:
                    wait = min(int(retry_after) if retry_after else backoff, 30)
                except ValueError:
                    wait = min(backoff, 30)
                if attempt < max_retries - 1:
                    logger.warning(
                        "IUCN API 429 for %s %s, retrying in %ss (attempt %s/%s)",
                        genus_name, species_name, wait, attempt + 1, max_retries
                    )
                    time.sleep(wait)
                    backoff *= 2
                    continue
                raise IUCNRateLimitError(
                    f"IUCN API rate limit hit for {genus_name} {species_name}"
                )
            response.raise_for_status()
            return response.json()
        except IUCNRateLimitError:
            raise
        except (HTTPError, SSLError,
                requests.exceptions.JSONDecodeError,
                requests.exceptions.RequestException) as e:
            logger.error(f"IUCN API error: {e}")
            return None


def fetch_iucn_data_by_sis_id(sis_id):
    """
    Fetch IUCN data using the IUCN taxon id (sis_id) and return the JSON
    payload.

    :param sis_id: IUCN taxon id (Taxonomy.iucn_redlist_id)
    :return: dict or None
    """
    api_iucn_key = preferences.SiteSetting.iucn_api_key

    if not api_iucn_key or not sis_id:
        return None

    url = "https://api.iucnredlist.org/api/v4/taxa/sis/{}".format(sis_id)
    headers = {
        'accept': 'application/json',
        'Authorization': api_iucn_key
    }

    max_retries = 4
    backoff = 2  # seconds, doubled on each 429
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 429:
                # Rate limited. Honour Retry-After if present, else backoff.
                retry_after = response.headers.get('Retry-After')
                try:
                    wait = min(int(retry_after) if retry_after else backoff, 30)
                except ValueError:
                    wait = min(backoff, 30)
                if attempt < max_retries - 1:
                    logger.warning(
                        "IUCN API 429 for sis_id=%s, retrying in %ss "
                        "(attempt %s/%s)", sis_id, wait, attempt + 1, max_retries
                    )
                    time.sleep(wait)
                    backoff *= 2
                    continue
                raise IUCNRateLimitError(
                    f"IUCN API rate limit hit for sis_id={sis_id}"
                )
            response.raise_for_status()
            return response.json()
        except (HTTPError, SSLError,
                requests.exceptions.JSONDecodeError,
                requests.exceptions.RequestException) as e:
            logger.error(f"IUCN API error: {e}")
            return None


def get_global_iucn_status(category):
    """
    Return the global (national=False) IUCNStatus for a category code,
    creating it if needed and tolerating pre-existing duplicates.

    :param category: red list category code (e.g. 'EN')
    :return: IUCNStatus or None
    """
    if not category:
        return None
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
    return iucn_status


def parse_latest_global_status(json_result):
    """
    Parse an IUCN taxa payload and return the latest global status.

    :param json_result: dict returned by the IUCN taxa endpoints
    :return: tuple (IUCNStatus or None, sis_id or None, iucn_url or None)
    """
    if not json_result:
        return None, None, None

    sis_id = json_result.get("taxon", {}).get("sis_id")

    assessments = json_result.get("assessments", [])
    latest = next((a for a in assessments if a.get("latest")), None)

    if latest:
        category = latest.get("red_list_category_code")
        iucn_url = latest.get("url")
        if category:
            return get_global_iucn_status(category), sis_id, iucn_url
        return None, sis_id, iucn_url

    return None, sis_id, None


def get_iucn_status(taxon):
    """
    Fetch IUCN status using genus/species name and return both
    IUCNStatus instance and sis_id (to set iucn_redlist_id manually).

    :param taxon: Taxonomy instance (must have genus_name and species_name)
    :return: tuple (IUCNStatus or None, sis_id or None, iucn_url or None)
    """
    return parse_latest_global_status(fetch_iucn_data(taxon))


def get_iucn_status_by_sis_id(sis_id):
    """
    Fetch the latest global IUCN status using the IUCN taxon id (sis_id).

    :param sis_id: IUCN taxon id (Taxonomy.iucn_redlist_id)
    :return: tuple (IUCNStatus or None, sis_id or None, iucn_url or None)
    """
    return parse_latest_global_status(fetch_iucn_data_by_sis_id(sis_id))


def get_iucn_assessments(taxon, json_result=None):
    """
    Fetch IUCN assessments using genus/species name and return assessments
    plus the IUCN sis_id.

    :param taxon: Taxonomy instance (must have genus_name and species_name)
    :param json_result: Pre-fetched IUCN API response dict (avoids a second API call)
    :return: tuple (assessments list, sis_id or None)
    """
    if json_result is None:
        json_result = fetch_iucn_data(taxon)
    if not json_result:
        return [], None

    sis_id = json_result.get("taxon", {}).get("sis_id")
    assessments = json_result.get("assessments", [])
    return assessments, sis_id
