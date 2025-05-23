# coding: utf-8
import csv
import io
import json
import asyncio
import os
import time
import zipfile
from pathlib import Path
from typing import TextIO, Optional, Set, List

import requests
import logging
import urllib
import simplejson
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from requests.exceptions import HTTPError
from pygbif import species
from pygbif.occurrences import search
from bims.models.taxonomy import Taxonomy
from bims.models.vernacular_name import VernacularName
from bims.enums import TaxonomicRank, TaxonomicStatus
from bims.models.harvest_session import HarvestSession

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
    Find species from gbif with lookup query.
    :param original_species_name: the name of species we want to find
    :param rank: taxonomy rank
    :param returns_all: returns all response
    :param classifier: rank classifier
    :return: List of species
    """
    print('Find species : %s' % original_species_name)
    try:
        response = species.name_lookup(
            q=original_species_name,
            limit=50,
            rank=rank
        )
        accepted_data = None
        synonym_data = None
        other_data = None
        if 'results' in response:
            results = response['results']
            if returns_all:
                return results
            for result in results:
                if classifier:
                    classifier_found = True
                    for key, value in classifier.items():
                        if value:
                            classifier_found = False
                            if key == 'class_name':
                                key = 'class'
                            if key not in result:
                                continue
                            if value.lower() == result[key].lower():
                                classifier_found = True
                    if not classifier_found:
                        continue
                rank = result.get('rank', '')
                if rank.lower() in RANK_KEYS:
                    rank_key = rank.lower() + 'Key'
                else:
                    rank_key = 'key'
                key_found = (
                        'nubKey' in result or rank_key in result)
                if key_found and 'taxonomicStatus' in result:
                    taxon_name = ''
                    if 'canonicalName' in result:
                        taxon_name = result['canonicalName']
                    if not taxon_name and rank.lower() in result:
                        taxon_name = result[rank.lower()]
                    if not taxon_name and 'scientificName' in result:
                        taxon_name = result['scientificName']

                    if result['taxonomicStatus'] == 'ACCEPTED':
                        if accepted_data:
                            if taxon_name == original_species_name:
                                if result['key'] < accepted_data['key']:
                                    accepted_data = result
                        else:
                            accepted_data = result
                    if result['taxonomicStatus'] == 'SYNONYM':
                        if synonym_data:
                            if taxon_name == original_species_name:
                                if result['key'] < synonym_data['key']:
                                    synonym_data = result
                        else:
                            synonym_data = result
                    else:
                        if other_data:
                            if taxon_name == original_species_name:
                                if result['key'] < other_data['key']:
                                    other_data = result
                        else:
                            other_data = result
        if accepted_data:
            return accepted_data
        if synonym_data:
            return synonym_data
        return other_data
    except HTTPError:
        print('Species not found')
    except AttributeError:
        print('error')

    return None


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
    print('Get taxon for key : %s' % key)

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

    try:
        print('Found detail for %s' % detail['scientificName'])
        taxon, status = Taxonomy.objects.get_or_create(
            gbif_key=detail['key'],
            scientific_name=detail['scientificName'],
            canonical_name=detail['canonicalName'],
            taxonomic_status=TaxonomicStatus[
                detail['taxonomicStatus']].name,
            rank=TaxonomicRank[
                detail['rank']].name,
        )
        taxon.gbif_data = detail
        taxon.save()

        # Get vernacular names
        if get_vernacular:
            vernacular_names = get_vernacular_names(detail['key'])
            if vernacular_names:
                print('Found %s vernacular names' % len(
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
        print(e)
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


GBIF_DOWNLOAD_URL = "https://api.gbif.org/v1/occurrence/download"
GBIF_REQUEST_URL  = f"{GBIF_DOWNLOAD_URL}/request"

def find_species_by_area(
        boundary_id: int,
        parent_species: Taxonomy,
        max_limit: Optional[int] = None,
        harvest_session: Optional[HarvestSession] = None,
        validated: bool = True,
        gbif_username: Optional[str] = None,
        gbif_password: Optional[str] = None,
) -> List[Taxonomy]:
    """
    Retrieves all species inside *boundary_id* (descendants of *parent_species*)
    using the GBIF Occurrence Download API, stores each DWCA archive in
    ``MEDIA_ROOT/gbif_downloads/`` and returns a list of local Taxonomy objects.
    """
    from bims.models.boundary import Boundary
    from bims.models.taxon_group_taxonomy import TaxonGroupTaxonomy
    from bims.models.taxon_group import TaxonGroup
    from bims.utils.fetch_gbif import fetch_all_species_from_gbif

    logger = logging.getLogger(__name__)

    # ---------------------------------------------------------------- helpers
    def _log(msg: str):
        logger.info(msg)
        if log_file_path:
            with open(log_file_path, "a") as lf:
                lf.write(f"{msg}\n")

    def _is_canceled() -> bool:
        if harvest_session:
            return HarvestSession.objects.get(id=harvest_session.id).canceled
        return False

    def _add_parent_to_group(taxon: Taxonomy, group: TaxonGroup):
        if taxon.parent:
            tgt, _ = TaxonGroupTaxonomy.objects.get_or_create(
                taxongroup=group, taxonomy=taxon
            )
            tgt.is_validated = validated
            tgt.save()
            _add_parent_to_group(taxon.parent, group)

    # ---------- GBIF interaction ------------------------------------------------
    def _submit_download(geometry_wkt: str) -> Optional[str]:
        predicate = {
            "type": "and",
            "predicates": [
                {"type": "equals", "key": "TAXON_KEY", "value": str(parent_species.gbif_key)},
                {"type": "within", "geometry": geometry_wkt},
                {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
                {"type": "equals", "key": "HAS_GEOSPATIAL_ISSUE", "value": "false"},
                {"type": "equals", "key": "BASIS_OF_RECORD", "value": "HUMAN_OBSERVATION"},
            ]
        }
        payload = {
            "creator": gbif_user,
            "sendNotification": False,
            "format": "DWCA",
            "description": f"Boundary {boundary_id} · parent {parent_species.scientific_name}",
            "predicate": predicate,
        }
        _log(f"POST {GBIF_REQUEST_URL}")
        r = requests.post(GBIF_REQUEST_URL, auth=auth, json=payload, timeout=60)
        if r.status_code != 201:
            _log(f"Download request failed ({r.status_code}): {r.text}")
            return None
        return r.text.strip().strip('"')

    def _get_ready_download_url(key: str) -> Optional[str]:
        """
        Polls the GBIF status endpoint until a *working* ZIP link is available.
        Returns the download URL, or ``None`` on failure/cancellation.
        """
        status_url = f"{GBIF_DOWNLOAD_URL}/{key}"
        poll_sec = 30

        while not _is_canceled():
            r = requests.get(status_url, auth=auth, timeout=30)
            if r.status_code != 200:
                _log(f"Status check failed ({r.status_code}): {r.text}")
                return None

            info = r.json()
            status = info.get("status", "UNKNOWN")
            link = info.get("downloadLink")

            _log(f"{key} status: {status} | link: {link}")

            # if GBIF already says it failed, stop here
            if status in {"FAILED", "KILLED", "CANCELLED"}:
                return None

            # Sometimes `status` is still RUNNING/PREPARING, but the file is ready.
            # Try the link (if present) until it responds with 200.
            if link:
                try:
                    # small request first to see if the file is materialised
                    probe = requests.get(link, auth=auth, stream=True, timeout=60)
                    if probe.status_code == 200:
                        probe.close()
                        return link
                    elif probe.status_code == 404:
                        # GBIF returns a JSON RemoteException when HDFS hasn't copied the file yet
                        _log("ZIP not yet in place, still waiting …")
                except Exception as exc:
                    _log(f"Probe failed: {exc}")

            time.sleep(poll_sec)

        return None

    def _wait_for_download(key: str) -> bool:
        status_url = f"{GBIF_DOWNLOAD_URL}/{key}"
        while not _is_canceled():
            r = requests.get(status_url, auth=auth, timeout=30)
            if r.status_code != 200:
                _log(f"Status check failed ({r.status_code}): {r.text}")
                return False
            status = r.json().get("status", "UNKNOWN")
            _log(f"{key} status: {status}")
            if status == "SUCCEEDED":
                return True
            if status in {"FAILED", "KILLED", "CANCELLED"}:
                return False
            time.sleep(30)
        return False

    def _download_archive(zip_url: str, key: str) -> Optional[Path]:
        """
        Streams the DWCA ZIP to MEDIA_ROOT/gbif_downloads/{key}.zip.
        Returns the Path (or None on error).
        """
        target_dir = Path(settings.MEDIA_ROOT) / "gbif_downloads"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{key}.zip"

        if target_path.exists():
            _log(f"Archive cached → {target_path}")
            return target_path

        _log(f"Downloading {zip_url}")
        try:
            with requests.get(zip_url, auth=auth, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                with open(target_path, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=8192):
                        fh.write(chunk)
            _log(f"Saved to {target_path}")
            return target_path
        except Exception as exc:
            _log(f"Failed to download archive {key}: {exc}")
            target_path.unlink(missing_ok=True)
            return None

    def _extract_species_keys(zip_path: Path, species_keys: Set[int]):
        with zipfile.ZipFile(zip_path) as zf:
            with zf.open("occurrence.txt") as occ_file:
                reader = csv.DictReader(io.TextIOWrapper(occ_file, encoding="utf-8"))
                for row in reader:
                    k = row.get("acceptedTaxonKey") or row.get("taxonKey")
                    if k and k.isdigit():
                        species_keys.add(int(k))
                        if max_limit and len(species_keys) >= max_limit:
                            return

    # ---------------------------------------------------------------- init vars
    species_keys: Set[int]       = set()
    species_found: List[Taxonomy] = []

    log_file_path = getattr(harvest_session.log_file, "path", None) if harvest_session else None
    taxon_group    = harvest_session.module_group if harvest_session else None

    gbif_user = gbif_username or os.getenv("GBIF_USERNAME")
    gbif_pass = gbif_password or os.getenv("GBIF_PASSWORD")
    if not gbif_user or not gbif_pass:
        raise RuntimeError("GBIF credentials missing (GBIF_USERNAME / GBIF_PASSWORD).")

    auth = (gbif_user, gbif_pass)

    # ---------------------------------------------------------------- geometry
    try:
        boundary = Boundary.objects.get(id=boundary_id)
        geometry = boundary.geometry
        if not geometry:
            raise ValueError("Boundary has no geometry")

        polygons = list(geometry) if isinstance(geometry, MultiPolygon) else [geometry]
        _log(f"Found {len(polygons)} polygon(s)")

        for idx, polygon in enumerate(polygons, start=1):
            if _is_canceled() or (max_limit and len(species_keys) >= max_limit):
                break
            geojson = json.loads(polygon.geojson)
            geojson["coordinates"] = round_coordinates(geojson["coordinates"])
            geom_wkt = GEOSGeometry(json.dumps(geojson)).wkt
            _log(f"Polygon {idx}/{len(polygons)}")

            key = _submit_download(geom_wkt)
            if not key:
                continue

            zip_url = _get_ready_download_url(key)
            if not zip_url:
                _log(f"Download {key} was not completed")
                continue

            zip_path = _download_archive(zip_url, key)
            if zip_path:
                _extract_species_keys(zip_path, species_keys)
                _log(f"Unique species keys: {len(species_keys)}")

            if max_limit and len(species_keys) >= max_limit:
                break

    except Boundary.DoesNotExist:
        logger.error(f"Boundary {boundary_id} does not exist.")
        return []
    except Exception as exc:
        logger.error(f"Boundary processing failed: {exc}")
        return []

    # ------------------------------------------------ fetch taxonomy objects
    for skey in species_keys:
        if _is_canceled():
            break
        try:
            _log(f"Processing {skey}")
            taxonomy = fetch_all_species_from_gbif(
                gbif_key=skey,
                fetch_children=False,
                log_file_path=log_file_path,
                fetch_vernacular_names=True,
            )
            if taxonomy:
                species_found.append(taxonomy)
                if taxon_group:
                    tgt, _ = TaxonGroupTaxonomy.objects.get_or_create(
                        taxongroup=taxon_group, taxonomy=taxonomy
                    )
                    tgt.is_validated = validated
                    tgt.save()
                    _add_parent_to_group(taxonomy, taxon_group)
        except Exception as exc:
            _log(f"Error fetching taxonomy {skey}: {exc}")

    _log(f"Species found: {len(species_found)}")
    return species_found
