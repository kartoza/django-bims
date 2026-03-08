import logging
import time

import requests
from requests.exceptions import HTTPError, SSLError

from bims.models.iucn_status import IUCNStatus
from preferences import preferences


logger = logging.getLogger(__name__)

IUCN_API_BASE = "https://api.iucnredlist.org/api/v4"

# ---------------------------------------------------------------------------
# IUCN taxon-group definitions
# Each entry maps a friendly group name to a list of taxonomy lookups.
# Each lookup specifies the taxonomy level ("class", "order", or "phylum")
# and the name to pass to the corresponding IUCN API v4 endpoint:
#   /api/v4/taxa/class/{name}
#   /api/v4/taxa/order/{name}
#   /api/v4/taxa/phylum/{name}
# Multiple entries per group are fetched and deduplicated by sis_id.
# ---------------------------------------------------------------------------
IUCN_TAXON_GROUPS = {
    "Freshwater fish": [
        {"level": "class", "name": "Actinopterygii"},
        {"level": "class", "name": "Chondrichthyes"},
    ],
    "Amphibia": [
        {"level": "class", "name": "Amphibia"},
    ],
    "Mollusca": [
        {"level": "phylum", "name": "Mollusca"},
    ],
    "Crustacea": [
        {"level": "class", "name": "Malacostraca"},
        {"level": "class", "name": "Maxillopoda"},
        {"level": "class", "name": "Branchiopoda"},
        {"level": "class", "name": "Ostracoda"},
    ],
    "Odonata": [
        {"level": "order", "name": "Odonata"},
    ],
}


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

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except (HTTPError, SSLError,
            requests.exceptions.JSONDecodeError,
            requests.exceptions.RequestException) as e:
        logger.error(f"IUCN API error: {e}")
        return None


def get_iucn_status(taxon):
    """
    Fetch IUCN status using genus/species name and return both
    IUCNStatus instance and sis_id (to set iucn_redlist_id manually).

    :param taxon: Taxonomy instance (must have genus_name and species_name)
    :return: tuple (IUCNStatus or None, sis_id or None, iucn_url or None)
    """
    iucn_url = None
    json_result = fetch_iucn_data(taxon)
    if not json_result:
        return None, None, None

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


def get_iucn_assessments(taxon):
    """
    Fetch IUCN assessments using genus/species name and return assessments
    plus the IUCN sis_id.

    :param taxon: Taxonomy instance (must have genus_name and species_name)
    :return: tuple (assessments list, sis_id or None)
    """
    json_result = fetch_iucn_data(taxon)
    if not json_result:
        return [], None

    sis_id = json_result.get("taxon", {}).get("sis_id")
    assessments = json_result.get("assessments", [])
    return assessments, sis_id


# ---------------------------------------------------------------------------
# IUCN bulk harvest
# ---------------------------------------------------------------------------

def _paginate_assessments(
    url: str,
    headers: dict,
    params: dict,
    label: str,
    latest: bool,
    max_pages: int | None,
    request_delay: float,
) -> set:
    """
    Paginate through an IUCN API endpoint that returns {"assessments": [...]}
    and collect the set of sis_taxon_ids found.
    """
    sis_ids = set()
    page_params = {**params, "page": 1}
    if latest:
        page_params["latest"] = "true"

    while True:
        try:
            response = requests.get(url, headers=headers, params=page_params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except (HTTPError, SSLError,
                requests.exceptions.JSONDecodeError,
                requests.exceptions.RequestException) as exc:
            logger.error("IUCN API error [%s, page=%s]: %s", label, page_params["page"], exc)
            break

        assessments_page = data.get("assessments", [])
        for assessment in assessments_page:
            sis_taxon_id = assessment.get("sis_taxon_id")
            if sis_taxon_id:
                sis_ids.add(sis_taxon_id)

        logger.info(
            "  [%s] page=%s | %s assessments | running total: %s sis_taxon_ids",
            label, page_params["page"], len(assessments_page), len(sis_ids),
        )

        if max_pages and page_params["page"] >= max_pages:
            break

        total_pages = data.get("total_pages") or data.get("pages")
        if total_pages is not None:
            if page_params["page"] >= int(total_pages):
                break
        elif not assessments_page:
            break

        page_params["page"] += 1
        if request_delay:
            time.sleep(request_delay)

    return sis_ids


def fetch_habitat_codes(headers: dict) -> list:
    """
    Return the list of habitat objects from GET /api/v4/habitats/.

    Each item typically contains 'code' and a description/name.
    """
    url = f"{IUCN_API_BASE}/habitats/"
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except (HTTPError, SSLError,
            requests.exceptions.JSONDecodeError,
            requests.exceptions.RequestException) as exc:
        logger.error("Failed to fetch habitat codes: %s", exc)
        return []

    # Response may be a list or {"habitats": [...]}
    if isinstance(data, list):
        return data
    return data.get("habitats", [])


def fetch_sis_ids_by_habitat(
    headers: dict,
    habitat_name: str,
    latest: bool = True,
    max_pages: int | None = None,
    request_delay: float = 1.0,
) -> set:
    """
    Return the set of sis_taxon_ids whose habitat name contains `habitat_name`
    (case-insensitive substring match against the habitat description).

    Fetches all habitat codes from /api/v4/habitats/, filters by name, then
    paginates /api/v4/habitats/{code} for each matching code.

    Example:
        fetch_sis_ids_by_habitat(headers, "wetland")
        fetch_sis_ids_by_habitat(headers, "forest")

    :param headers:       Authorisation headers for the IUCN API.
    :param habitat_name:  Substring to match against habitat descriptions.
    :param latest:        Pass latest=true to each paginated call.
    :param max_pages:     Cap pages per habitat code (for testing).
    :param request_delay: Seconds to sleep between requests.
    :return: set of sis_taxon_ids present in any matching habitat.
    """
    habitat_list = fetch_habitat_codes(headers)
    if not habitat_list:
        logger.warning("No habitat codes returned; habitat filter will be empty.")
        return set()

    keyword = habitat_name.lower()
    matched_codes = []
    for h in habitat_list:
        # Description may be a plain string or a nested dict
        description = h.get("description") or h.get("name") or ""
        if isinstance(description, dict):
            description = " ".join(str(v) for v in description.values())
        if keyword in description.lower():
            matched_codes.append(h.get("code"))

    if not matched_codes:
        logger.warning("No habitat codes matched '%s'.", habitat_name)
        return set()

    logger.info("Habitat codes matching '%s': %s", habitat_name, matched_codes)

    sis_ids = set()
    for code in matched_codes:
        url = f"{IUCN_API_BASE}/habitats/{code}"
        ids = _paginate_assessments(
            url=url,
            headers=headers,
            params={},
            label=f"habitat/{code}",
            latest=latest,
            max_pages=max_pages,
            request_delay=request_delay,
        )
        sis_ids |= ids
        logger.info(
            "Habitat %s ('%s'): %s sis_taxon_ids (running total: %s)",
            code, habitat_name, len(ids), len(sis_ids),
        )

    return sis_ids


def harvest_iucn_taxa(
    group_names: list | None = None,
    habitat_name: str = "wetland",
    latest: bool = True,
    request_delay: float = 1.0,
    max_pages: int | None = None,
) -> dict:
    """
    Harvest taxa from the IUCN Red List API v4.

    For each taxon group:
      1. Collect sis_taxon_ids via taxonomy endpoints
         (GET /api/v4/taxa/class|order|phylum/{name})
      2. Collect sis_taxon_ids via habitat endpoints filtered by habitat_name
         (GET /api/v4/habitats/{code} for each matching habitat)
      3. Keep only the intersection (taxa present in both).

    :param group_names:   Groups to harvest; None = all groups in IUCN_TAXON_GROUPS.
    :param habitat_name:  Habitat name substring to filter by (default: "wetland").
    :param latest:        Pass latest=true to each API call.
    :param request_delay: Seconds to sleep between paginated requests.
    :param max_pages:     Stop after this many pages per endpoint (for testing).
    :return: dict  {group_name: [sis_taxon_id, ...]}
    """
    api_key = preferences.SiteSetting.iucn_api_key
    if not api_key:
        logger.error("IUCN API key is not configured in SiteSetting.")
        return {}

    headers = {
        "accept": "application/json",
        "Authorization": api_key,
    }

    groups_to_fetch = (
        {k: v for k, v in IUCN_TAXON_GROUPS.items() if k in group_names}
        if group_names
        else IUCN_TAXON_GROUPS
    )

    # Step 1: collect habitat sis_taxon_ids once (shared across all groups)
    logger.info("Fetching sis_taxon_ids for habitat '%s'...", habitat_name)
    wetland_ids = fetch_sis_ids_by_habitat(
        headers=headers,
        habitat_name=habitat_name,
        latest=latest,
        max_pages=max_pages,
        request_delay=request_delay,
    )
    logger.info("Total sis_taxon_ids for habitat '%s': %s", habitat_name, len(wetland_ids))

    results = {}

    for group_name, lookups in groups_to_fetch.items():
        logger.info("Harvesting taxonomy sis_taxon_ids for group: %s", group_name)
        taxonomy_ids = set()

        for lookup in lookups:
            level = lookup["level"]
            name = lookup["name"]
            url = f"{IUCN_API_BASE}/taxa/{level}/{name}"
            ids = _paginate_assessments(
                url=url,
                headers=headers,
                params={},
                label=f"{level}/{name}",
                latest=latest,
                max_pages=max_pages,
                request_delay=request_delay,
            )
            taxonomy_ids |= ids

        # Step 2: intersect with wetland ids
        matched = taxonomy_ids & wetland_ids
        results[group_name] = sorted(matched)
        logger.info(
            "Group '%s': %s taxonomy ids, %s after wetland filter.",
            group_name, len(taxonomy_ids), len(matched),
        )

    return results
