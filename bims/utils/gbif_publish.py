# utils/gbif_publish.py
import csv
import os
import zipfile
import uuid
from datetime import datetime
from typing import Iterable, Tuple, List

import requests
from django.conf import settings
from django.db import transaction
from django.utils.timezone import now
from requests.auth import HTTPBasicAuth

from bims.models.biological_collection_record import BiologicalCollectionRecord

GBIF_TEST_API = "https://api.gbif-test.org/v1"
LICENSE_URL = getattr(
    settings, "GBIF_DATASET_LICENSE",
    "https://creativecommons.org/publicdomain/zero/1.0/legalcode"
)

def _base_url() -> str:
    return getattr(settings, "GBIF_EXPORT_BASE_URL", "").rstrip("/")

def _media_url() -> str:
    return getattr(settings, "MEDIA_URL", "/media/").rstrip("/")

def _site_name() -> str:
    return getattr(settings, "SITE_NAME", "BIMS")

def _gbif_auth() -> HTTPBasicAuth:
    user = getattr(settings, "GBIF_TEST_USERNAME", "")
    pwd = getattr(settings, "GBIF_TEST_PASSWORD", "")
    return HTTPBasicAuth(user, pwd)

PUBLISHING_ORG_KEY = getattr(settings, "GBIF_TEST_PUBLISHING_ORG_KEY", "")
INSTALLATION_KEY = getattr(settings, "GBIF_TEST_INSTALLATION_KEY", "")


def gather_data() -> Iterable[BiologicalCollectionRecord]:
    return (
        BiologicalCollectionRecord.objects
        .filter(validated=True, data_type="public")
        .exclude(source_collection__iexact="gbif")
        .select_related("taxonomy", "site", "record_type")
    )[:10]


def _lat_lon_from_site(site) -> Tuple[str, str]:
    if not site:
        return "", ""
    lat = getattr(site, "latitude", None)
    lon = getattr(site, "longitude", None)
    if lat is not None and lon is not None:
        return str(lat), str(lon)
    return "", ""


def _dwca_dir() -> str:
    ts = now().strftime("%Y%m%d-%H%M%S")
    rel = os.path.join("exports", "gbif", ts + "-" + uuid.uuid4().hex[:8])
    abs_dir = os.path.join(settings.MEDIA_ROOT, rel)
    os.makedirs(abs_dir, exist_ok=True)
    return abs_dir

def _write_occurrence_txt(path: str, records: Iterable[BiologicalCollectionRecord]) -> List[int]:
    header = [
        "occurrenceID", "basisOfRecord", "scientificName", "eventDate",
        "decimalLatitude", "decimalLongitude", "locality", "recordedBy",
        "datasetName", "institutionCode", "collectionCode", "catalogNumber",
        "dataGeneralizations"
    ]
    written_ids: List[int] = []
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(header)
        for r in records:
            # Skip if no taxon
            sci_name = (
                    getattr(r.taxonomy, "canonical_name", None) or
                    r.original_species_name or ""
            ).strip()
            if not sci_name:
                continue

            lat, lon = _lat_lon_from_site(r.site)
            locality = getattr(r.site, "name", "") or getattr(r.site, "site_name", "") or ""
            basis = "HUMAN_OBSERVATION"
            try:
                rt = (r.record_type.name or "").lower()
                if "sample" in rt:
                    basis = "MATERIAL_SAMPLE"
                elif "observation" in rt or "visual" in rt:
                    basis = "HUMAN_OBSERVATION"
            except Exception:
                pass

            occurrence_id = str(r.uuid or r.pk)
            collection_code = (getattr(getattr(r, "module_group", None), "name", "") or "BIMS")
            catalog_number = str(r.pk)

            recorded_by = (r.collector or r.identified_by or "").strip()
            dataset_name = f"{_site_name()} Occurrence Export {datetime.utcnow().date().isoformat()}"
            inst_code = (r.institution_id or "").strip()
            dg = ""

            event_date = ""
            if r.collection_date:
                event_date = r.collection_date.isoformat()

            row = [
                "bims" + occurrence_id, basis, sci_name, event_date,
                lat, lon, locality, recorded_by,
                dataset_name, inst_code, collection_code, catalog_number,
                dg
            ]
            w.writerow(row)
            written_ids.append(r.id)
    return written_ids

def _write_meta_xml(path: str):
    meta = f"""<archive xmlns="http://rs.tdwg.org/dwc/text/" metadata="eml.xml">
      <core encoding="UTF-8" fieldsTerminatedBy="\\t" linesTerminatedBy="\\n" fieldsEnclosedBy="" ignoreHeaderLines="1" rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
        <files><location>occurrence.txt</location></files>
        <id index="0"/>
        <field index="0"  term="http://rs.tdwg.org/dwc/terms/occurrenceID"/>
        <field index="1"  term="http://rs.tdwg.org/dwc/terms/basisOfRecord"/>
        <field index="2"  term="http://rs.tdwg.org/dwc/terms/scientificName"/>
        <field index="3"  term="http://rs.tdwg.org/dwc/terms/eventDate"/>
        <field index="4"  term="http://rs.tdwg.org/dwc/terms/decimalLatitude"/>
        <field index="5"  term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>
        <field index="6"  term="http://rs.tdwg.org/dwc/terms/locality"/>
        <field index="7"  term="http://rs.tdwg.org/dwc/terms/recordedBy"/>
        <field index="8"  term="http://rs.tdwg.org/dwc/terms/datasetName"/>
        <field index="9"  term="http://rs.tdwg.org/dwc/terms/institutionCode"/>
        <field index="10" term="http://rs.tdwg.org/dwc/terms/collectionCode"/>
        <field index="11" term="http://rs.tdwg.org/dwc/terms/catalogNumber"/>
        <field index="12" term="http://rs.tdwg.org/dwc/terms/dataGeneralizations"/>
      </core>
    </archive>
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(meta)

def _write_eml_xml(path: str, title: str, abstract: str):
    today = datetime.utcnow().date().isoformat()
    eml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <eml:eml packageId="{uuid.uuid4()}" system="GBIF" xmlns:eml="eml://ecoinformatics.org/eml-2.1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="eml://ecoinformatics.org/eml-2.1.1 http://rs.gbif.org/schema/eml-gbif-profile/1.1/eml.xsd">
      <dataset>
        <title>{title}</title>
        <creator>
          <individualName>
            <surName>{_site_name()}</surName>
          </individualName>
          <organizationName>{_site_name()}</organizationName>
        </creator>
        <metadataProvider>
          <individualName>
            <surName>{_site_name()}</surName>
          </individualName>
        </metadataProvider>
        <pubDate>{today}</pubDate>
        <abstract><para>{abstract}</para></abstract>
        <intellectualRights>
          <para>{LICENSE_URL}</para>
        </intellectualRights>
      </dataset>
    </eml:eml>
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(eml)

def _zip_dwca(folder: str) -> str:
    zip_path = os.path.join(folder, "dwca.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for fname in ["occurrence.txt", "meta.xml", "eml.xml"]:
            z.write(os.path.join(folder, fname), arcname=fname)
    return zip_path

def _build_dwca(records: Iterable[BiologicalCollectionRecord]) -> Tuple[str, str, List[int]]:
    out_dir = _dwca_dir()
    occ_path = os.path.join(out_dir, "occurrence.txt")
    meta_path = os.path.join(out_dir, "meta.xml")
    eml_path = os.path.join(out_dir, "eml.xml")

    written_ids = _write_occurrence_txt(occ_path, records)
    if not written_ids:
        raise ValueError("No eligible records to export.")

    title = f"{_site_name()} test export ({datetime.utcnow().isoformat(timespec='seconds')} UTC)"
    abstract = "Automated occurrence export from BIMS for GBIF-Test ingestion."
    _write_meta_xml(meta_path)
    _write_eml_xml(eml_path, title, abstract)
    zip_path = _zip_dwca(out_dir)

    rel_media = os.path.relpath(zip_path, settings.MEDIA_ROOT)
    archive_url = f"{_base_url()}{_media_url()}/{rel_media}".replace("//", "/").replace(":/", "://")
    return zip_path, archive_url, written_ids


def _register_dataset_on_gbif_test(title: str, description: str, license_url: str) -> str:
    if not PUBLISHING_ORG_KEY or not INSTALLATION_KEY:
        raise RuntimeError("Missing GBIF_TEST_PUBLISHING_ORG_KEY or GBIF_TEST_INSTALLATION_KEY in settings.")

    payload = {
        "publishingOrganizationKey": PUBLISHING_ORG_KEY,
        "installationKey": INSTALLATION_KEY,
        "type": "OCCURRENCE",
        "title": title,
        "description": description,
        "language": "eng",
        "license": license_url,
    }
    r = requests.post(
        f"{GBIF_TEST_API}/dataset",
        json=payload,
        auth=_gbif_auth(),
        timeout=30,
        headers={"Content-Type": "application/json"},
    )
    r.raise_for_status()
    dataset_key = r.json()
    if not isinstance(dataset_key, str) or len(dataset_key) < 32:
        raise RuntimeError(f"Unexpected dataset key response: {dataset_key}")
    return dataset_key

def _add_endpoint(dataset_key: str, archive_url: str):
    payload = {
        "type": "DWC_ARCHIVE",
        "url": archive_url,
    }
    r = requests.post(
        f"{GBIF_TEST_API}/dataset/{dataset_key}/endpoint",
        json=payload,
        auth=_gbif_auth(),
        timeout=30,
        headers={"Content-Type": "application/json"},
    )
    r.raise_for_status()


@transaction.atomic
def publish_gbif_data() -> str:
    """
    Build a DwC-A for 10 public, validated records, register it on GBIF-Test,
    add the DWC_ARCHIVE endpoint, and store dataset_key back to those records.

    Returns the dataset UUID (dataset_key).
    """
    records = list(gather_data())
    if not records:
        raise ValueError("No records to publish (need public+validated).")

    zip_path, archive_url, written_ids = _build_dwca(records)

    title = f"{_site_name()} occurrence dataset (test)"
    description = "Minimal test dataset registered via the GBIF-Test API. Data generated from BIMS."

    dataset_key = _register_dataset_on_gbif_test(
        title, description, LICENSE_URL
    )
    _add_endpoint(dataset_key, archive_url)

    BiologicalCollectionRecord.objects.filter(
        id__in=written_ids
    ).update(dataset_key=dataset_key)

    return dataset_key
