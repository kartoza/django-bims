# coding: utf-8
import requests
import logging
import urllib
import simplejson
from requests.exceptions import HTTPError
from requests.adapters import HTTPAdapter, Retry
from pygbif import species
from bims.models.taxonomy import Taxonomy
from bims.models.vernacular_name import VernacularName
from bims.enums import TaxonomicRank, TaxonomicStatus
from bims.utils.logger import log


GBIF_API = "https://api.gbif.org/v1"

logger = logging.getLogger(__name__)

RANK_KEYS = [
    'kingdom',
    'phylum',
    'class',
    'order',
    'family'
]


def update_taxa():
    """Get all taxon, then update the data based on the gbif id."""
    taxa = Taxonomy.objects.all()
    if not taxa:
        print('No taxon found')
    for taxon in taxa:
        print('Update taxon for %s with gbif id %s' % (
            taxon.common_name, taxon.gbif_id))
        try:
            response = species.name_usage(key=taxon.gbif_id)
            if response:
                update_taxonomy_fields(taxon, response)
                print('Taxon updated')
        except HTTPError as e:
            print('Taxon not updated')
            print(e)


def get_species(gbif_id):
    """
    Get species by gbif id
    :param gbif_id: gbif id
    :return: species dictionary
    """
    api_url = 'http://api.gbif.org/v1/species/' + str(gbif_id)
    try:
        response = requests.get(api_url)
        json_result = response.json()
        return json_result
    except (HTTPError, KeyError, simplejson.errors.JSONDecodeError) as e:
        print(e)
        return None


def get_vernacular_names(species_id):
    """
    Get vernacular names from species id
    :param species_id: taxonomy id
    :return: array of vernacular name
    """
    api_url = 'http://api.gbif.org/v1/species/%s/vernacularNames' % (
        str(species_id)
    )
    try:
        response = requests.get(api_url)
        json_result = response.json()
        return json_result
    except (HTTPError, KeyError, simplejson.errors.JSONDecodeError) as e:
        print(e)
        return None


def get_children(key):
    """
    Lists all direct child usages for a name usage
    :return: list of species
    """
    api_url = 'http://api.gbif.org/v1/species/{key}/children'.format(
        key=key
    )
    try:
        response = requests.get(api_url)
        json_response = response.json()
        if json_response['results']:
            return json_response['results']
        return None
    except (HTTPError, KeyError) as e:
        print(e)
        return None


def find_species(
        original_species_name,
        rank=None,
        returns_all=False,
        **classifier):
    """
    GBIF lookup that prefers canonical backbone data.
    - Filters by optional classifier kwargs (e.g., class_name='Actinopteri').
    - Picks best candidate by status > exact match > nubKey > parentKey > smallest key.
    - Resolves to /species/{nubKey} (backbone). If UNRANKED, returns its parent.
    """
    logger.info('Find species : %s', original_species_name)
    try:
        resp = species.name_lookup(q=original_species_name, limit=50, rank=rank)
    except HTTPError:
        logger.warning('Species not found (HTTPError) for %s', original_species_name)
        return None
    except Exception as e:
        logger.warning('Lookup error for %s: %s', original_species_name, e)
        return None

    if not resp or 'results' not in resp:
        return None
    results = resp['results']
    if returns_all:
        return results

    def _matches_classifier(r: dict) -> bool:
        if not classifier:
            return True
        for k, v in classifier.items():
            if not v:
                continue
            key_db = 'class' if k == 'class_name' else k
            if (r.get(key_db) or '').lower() != str(v).lower():
                return False
        return True

    accepted_best = None
    synonym_best = None
    other_best = None

    for r in results:
        if not _matches_classifier(r):
            continue

        rk = (r.get('rank') or '').lower()
        rank_key = (rk + 'Key') if rk in RANK_KEYS else 'key'
        has_any_key = ('nubKey' in r) or (rank_key in r) or ('key' in r)
        if not has_any_key or 'taxonomicStatus' not in r:
            continue

        status = r['taxonomicStatus']
        if status == 'ACCEPTED':
            accepted_best = _prefer(r, accepted_best, original_species_name)
            if accepted_best and accepted_best.get('nubKey'):
                break
        elif status == 'SYNONYM':
            synonym_best = _prefer(r, synonym_best, original_species_name)
        else:
            other_best = _prefer(r, other_best, original_species_name)

    chosen = accepted_best or synonym_best or other_best
    if not chosen:
        return None

    detail_key = chosen.get('nubKey') or chosen.get('key')
    if not detail_key:
        return chosen

    detail = get_species(detail_key)
    if not detail:
        return chosen

    nub_key = detail.get('nubKey')
    if nub_key and nub_key != detail.get('key'):
        canonical = get_species(nub_key)
        if canonical:
            detail = canonical

    if (detail.get('rank') or '').upper() == 'UNRANKED':
        parent_key = detail.get('parentKey')
        if parent_key:
            parent_detail = get_species(parent_key)
            if parent_detail:
                detail = parent_detail

    return detail


def _prefer(candidate, current, original_name):
    """
    Prefer better GBIF lookup candidates within the same status bucket.
    Priority:
      1) exact name match (canonical/scientific) to original_name
      2) has nubKey
      3) has parentKey
      4) smaller 'key'
    """
    if current is None:
        return candidate

    def _norm(s):
        return (s or '').strip().lower()

    cand_name = _norm(candidate.get('canonicalName') or candidate.get('scientificName'))
    curr_name = _norm(current.get('canonicalName') or current.get('scientificName'))
    orig      = _norm(original_name)

    cand_exact = (cand_name == orig)
    curr_exact = (curr_name == orig)

    if cand_exact != curr_exact:
        return candidate if cand_exact else current

    cand_has_nub = 'nubKey' in candidate and candidate.get('nubKey') is not None
    curr_has_nub = 'nubKey' in current and current.get('nubKey') is not None
    if cand_has_nub != curr_has_nub:
        return candidate if cand_has_nub else current

    cand_has_parent = 'parentKey' in candidate and candidate.get('parentKey') is not None
    curr_has_parent = 'parentKey' in current and current.get('parentKey') is not None
    if cand_has_parent != curr_has_parent:
        return candidate if cand_has_parent else current

    try:
        return candidate if int(candidate.get('key', 10**12)) < int(current.get('key', 10**12)) else current
    except Exception:
        return candidate


def search_exact_match(species_name):
    """
    Search species detail
    :param species_name: species name
    :return: species detail if found
    """
    api_url = 'http://api.gbif.org/v1/species/match?name=' + str(species_name)
    try:
        response = requests.get(api_url)
        json_result = response.json()
        if json_result and 'usageKey' in json_result:
            key = json_result['usageKey']
            return key
        return None
    except (HTTPError, KeyError) as e:
        print(e)
        return None


def update_collection_record(collection):
    """
    Update taxon for a collection.
    :param collection: Biological collection record model
    """

    taxonomy = Taxonomy.objects.filter(
        scientific_name__contains=collection.original_species_name
    )
    if taxonomy:
        print('%s exists in Taxonomy' % collection.original_species_name)
        collection.taxonomy = taxonomy[0]
        collection.save()
        return

    result = find_species(collection.original_species_name)

    if not result:
        return

    if 'nubKey' in result:
        taxon_key = result['nubKey']
    elif 'speciesKey' in result:
        taxon_key = result['speciesKey']
    else:
        return

    taxonomy = update_taxonomy_from_gbif(taxon_key)
    collection.taxonomy = taxonomy
    collection.save()


def update_taxonomy_fields(taxon, response):
    """Helper to update taxonomy field of taxon from a response dictionary.

    :param taxon: The Taxon object.
    :type taxon: Taxon

    :param response: A dictionary contains of Taxonomy value.
    :type response: dict
    """
    # Iterate through all fields and update the one which is a
    # field from Taxonomy
    taxon_fields = Taxonomy._meta.get_fields()
    for field in taxon_fields:
        # Set vernacular names
        try:
            if field.get_attname() == 'vernacular_names':
                vernacular_names = []
                for vernacular_name in response['vernacularNames']:
                    if 'vernacularName' in vernacular_name:
                        vernacular_names.append(
                            vernacular_name['vernacularName']
                        )
                taxon.vernacular_names = vernacular_names
        except (AttributeError, KeyError) as e:
            print(e)
            continue

    taxon.save()


def update_taxonomy_from_gbif(key, fetch_parent=True, get_vernacular=True):
    """
    Update taxonomy data with data from gbif
    :param key: gbif key
    :param fetch_parent: whether need to fetch parent, default to True
    :param get_vernacular: get vernacular names
    :return:
    """
    # Get taxon
    log('Get taxon for key : %s' % key)

    try:
        taxon = Taxonomy.objects.get(
            gbif_key=key,
            scientific_name__isnull=False
        )
        if taxon.parent or taxon.rank == 'KINGDOM':
            return taxon
    except Taxonomy.DoesNotExist:
        pass

    detail = get_species(key)
    taxon = None
    accepted_taxon = None

    # If synonym then get the accepted taxon
    if 'synonym' in detail['taxonomicStatus'].lower():
        accepted_taxon_key = detail.get('acceptedKey', '')
        if accepted_taxon_key:
            accepted_taxon = Taxonomy.objects.filter(
                gbif_key=accepted_taxon_key
            ).first()
            if not accepted_taxon:
                accepted_taxon = update_taxonomy_from_gbif(
                    accepted_taxon_key,
                    get_vernacular=get_vernacular
                )

    try:
        log('Found detail for %s' % detail['scientificName'])
        taxon, status = Taxonomy.objects.get_or_create(
            gbif_key=detail['key'],
            scientific_name=detail['scientificName'],
            canonical_name=detail['canonicalName'],
            taxonomic_status=TaxonomicStatus[
                detail['taxonomicStatus']].name,
            rank=TaxonomicRank[
                detail['rank']].name,
            author=detail.get('authorship', '')
        )
        taxon.gbif_data = detail
        if accepted_taxon:
            taxon.accepted_taxonomy = accepted_taxon
        taxon.save()

        # Get vernacular names
        if get_vernacular:
            vernacular_names = get_vernacular_names(detail['key'])
            if vernacular_names:
                log('Found %s vernacular names' % len(
                    vernacular_names['results']))
                for result in vernacular_names['results']:
                    fields = {}
                    if 'source' in result:
                        fields['source'] = result['source']
                    if 'language' in result:
                        fields['language'] = result['language']
                    if 'taxonKey' in result:
                        fields['taxon_key'] = int(result['taxonKey'])
                    vernacular_name, status = (
                        VernacularName.objects.get_or_create(
                            name=result['vernacularName'],
                            **fields
                        )
                    )
                    taxon.vernacular_names.add(vernacular_name)
                taxon.save()

        if 'parentKey' in detail and fetch_parent:
            taxon.parent = update_taxonomy_from_gbif(
                detail['parentKey'],
                get_vernacular=get_vernacular
            )
            taxon.save()
    except (KeyError, TypeError) as e:
        pass

    return taxon


def search_taxon_identifier(search_query, fetch_parent=True):
    """
    Search from gbif api, then create taxon identifier
    :param search_query: string query
    :param fetch_parent: whether need to fetch parent, default to True
    :return:
    """
    print('Search for %s' % search_query)
    species_detail = None
    key = search_exact_match(search_query)

    if not key:
        species_detail = find_species(search_query)
        if not species_detail:
            return None
        rank = species_detail.get('rank', '')
        rank_key = rank.lower() + 'Key'

        if rank_key in species_detail:
            key = species_detail[rank_key]
        elif 'nubKey' in species_detail:
            key = species_detail['nubKey']

    if key:
        species_detail = update_taxonomy_from_gbif(key, fetch_parent)

    return species_detail


def suggest_search(query_params):
    """
    Search from gbif using suggestion api
    :param query_params: Query parameter
    :return: list of taxon
    """
    api_url = 'https://api.gbif.org/v1/species/suggest?{param}'.format(
        param=urllib.parse.urlencode(query_params)
    )
    try:
        response = requests.get(api_url)
        results = response.json()
        return results
    except (HTTPError, KeyError) as e:
        print(e)
        return None


def gbif_name_suggest(**kwargs):
    # Wrapper for pygbif name_suggest function
    response = species.name_suggest(**kwargs)
    if len(response) == 0:
        return None
    accepted_data = None
    synonym_data = None
    other_data = None
    for result in response:
        rank = result.get('rank', '')
        if rank.lower() in RANK_KEYS:
            rank_key = rank.lower() + 'Key'
        else:
            rank_key = 'key'
        key_found = (
                'nubKey' in result or rank_key in result)
        if key_found and 'status' in result:
            if result['status'] == 'ACCEPTED':
                if accepted_data:
                    if result['key'] < accepted_data['key']:
                        accepted_data = result
                else:
                    accepted_data = result
            if result['status'] == 'SYNONYM':
                if synonym_data:
                    if result['key'] < synonym_data['key']:
                        synonym_data = result
                else:
                    synonym_data = result
            else:
                if other_data:
                    if result['key'] < other_data['key']:
                        other_data = result
                else:
                    other_data = result
    if accepted_data:
        return accepted_data
    if synonym_data:
        return synonym_data
    return other_data


ACCEPTED_TAXON_KEY = 'acceptedTaxonKey'


def round_coordinates(coords):
    if isinstance(coords[0], list):
        return [round_coordinates(sub_coords) for sub_coords in coords]
    else:
        return [round(coord, 4) for coord in coords]


def _gbif_session():
    """Requests session with sane retries/backoff for GBIF."""
    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def gbif_synonyms_by_usage(
    usage_key: int,
    limit: int = 1000,
    accept_language: str | None = None,
) -> list[dict]:
    """
    Calls GBIF /v1/species/{usageKey}/synonyms and paginates until exhausted.
    Returns a flat list of synonym objects.
    """
    sess = _gbif_session()
    url = f"{GBIF_API}/species/{usage_key}/synonyms"
    headers = {}
    if accept_language:
        headers["Accept-Language"] = accept_language

    results: list[dict] = []
    offset = 0

    while True:
        resp = sess.get(
            url,
            params={"limit": limit, "offset": offset},
            headers=headers, timeout=60)
        resp.raise_for_status()
        page = resp.json() or []

        if not isinstance(page, list):
            page = (
                    page.get("results") or
                    page.get("synonyms") or []) if isinstance(page, dict) else []

        if not page:
            break

        results.extend(page)
        if len(page) < limit:
            break
        offset += limit

    return results
