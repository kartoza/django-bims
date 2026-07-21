# coding=utf-8
"""
Check whether GBIF-sourced data held locally still exists upstream in GBIF.

Three entity types are supported, each with a different (and non-obvious)
deletion signal from the GBIF API:

  occurrences
      GET /occurrence/{gbifID}. A 404 means the occurrence is no longer
      indexed by GBIF (effectively deleted). A 200 means it is still live.

  datasets
      GET /dataset/{key}. The registry keeps a tombstone: a non-null
      "deleted" timestamp field marks a deleted dataset.

  taxa
      GET /species/{key} is NOT reliable: it keeps serving stale backbone
      keys forever and never sets a "deleted" flag for them. Instead we
      re-match the name via /species/match and compare the current backbone
      usageKey with the stored gbif_key. A differing (or missing) usageKey
      means the stored key is a superseded/deleted backbone key.

The command only reports; it never modifies or deletes anything. Findings can
optionally be written to CSV with --output.
"""

import csv
import logging
from datetime import timedelta

import requests
from requests.adapters import HTTPAdapter, Retry
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.utils import timezone
from django_tenants.utils import get_tenant_model, tenant_context

from bims.models import AbstractTaxonomy
from bims.models.biological_collection_record import BiologicalCollectionRecord

logger = logging.getLogger(__name__)

GBIF_API = 'https://api.gbif.org/v1'
GBIF_API_V2 = 'https://api.gbif.org/v2'

VALID_CHECKS = ('taxa', 'datasets', 'occurrences')

MULTIPLE_MATCHES_SAME_CONFIDENCE = 'MULTIPLE_MATCHES_SAME_CONFIDENCE'


def build_session():
    """Requests session with sensible retries for the GBIF API."""
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(['GET']),
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session


class Command(BaseCommand):
    help = (
        "Report GBIF-sourced taxa, datasets and/or occurrences that appear to "
        "have been deleted or superseded upstream in GBIF."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            dest="checks",
            action="append",
            choices=VALID_CHECKS,
            help=(
                "Which entity type(s) to check. May be repeated. "
                "Defaults to all of: %s." % ', '.join(VALID_CHECKS)
            ),
        )
        parser.add_argument(
            "-s", "--schema-name",
            dest="schema_names",
            action="append",
            help="Limit to specific tenant schema(s). May be repeated.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max number of records to check per entity type (0 = no limit).",
        )
        parser.add_argument(
            "--stale-days",
            type=int,
            default=0,
            help=(
                "Only check occurrences whose modified_date is older than this "
                "many days (0 = no age filter). Records are checked "
                "oldest-modified first, so combined with --limit this budgets "
                "each run to the stalest records."
            ),
        )
        parser.add_argument(
            "--output",
            dest="output",
            help="Optional CSV path to write the findings to.",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Per-request timeout in seconds (default: 30).",
        )
        parser.add_argument(
            "--progress-every",
            type=int,
            default=100,
            help="Log progress after every N records checked (default: 100).",
        )

    def handle(self, *args, **options):
        checks = options.get("checks") or list(VALID_CHECKS)
        schema_names = options.get("schema_names") or []
        self.limit = options.get("limit") or 0
        self.stale_days = options.get("stale_days") or 0
        self.timeout = options.get("timeout") or 30
        self.progress_every = options.get("progress_every") or 100
        self.session = build_session()

        tenant_model = get_tenant_model()
        tenants = tenant_model.objects.all()
        if schema_names:
            tenants = tenants.filter(schema_name__in=schema_names)

        findings = []
        for tenant in tenants:
            with tenant_context(tenant):
                self.stdout.write(self.style.MIGRATE_HEADING(
                    "Schema: %s" % tenant.schema_name))
                if 'taxa' in checks:
                    findings += self.check_taxa(tenant.schema_name)
                if 'datasets' in checks:
                    findings += self.check_datasets(tenant.schema_name)
                if 'occurrences' in checks:
                    findings += self.check_occurrences(tenant.schema_name)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "Done. %d finding(s) across %d schema(s)." % (
                len(findings), tenants.count())))

        output = options.get("output")
        if output and findings:
            self.write_csv(output, findings)
            self.stdout.write(self.style.SUCCESS(
                "Findings written to %s" % output))

    def report_progress(self, label, processed, total, found):
        """Log progress after every --progress-every records, and at the end."""
        if processed % self.progress_every == 0 or processed == total:
            self.stdout.write(
                "  [%s] processed %d/%d (%d finding(s) so far)" % (
                    label, processed, total, found))

    # ------------------------------------------------------------------ taxa
    def check_taxa(self, schema_name):
        from bims.models.taxonomy import Taxonomy

        qs = Taxonomy.objects.filter(
            gbif_key__isnull=False,
            taxongrouptaxonomy__isnull=False,
        ).exclude(scientific_name='').distinct().order_by('id')
        if self.limit:
            qs = qs[:self.limit]

        total = qs.count()
        self.stdout.write("  [taxa] checking %d taxon(s)..." % total)
        findings = []
        processed = 0
        for taxon in qs.iterator():
            processed += 1
            self.report_progress('taxa', processed, total, len(findings))
            name = taxon.scientific_name or taxon.canonical_name
            data = self.match_taxon(name)

            if data is None:
                continue

            diagnostics = data.get('diagnostics') or {}
            match_type = diagnostics.get('matchType')
            processing_flags = diagnostics.get('processingFlags') or []
            current_key = (data.get('usage') or {}).get('key')

            if match_type in (None, 'NONE'):
                if MULTIPLE_MATCHES_SAME_CONFIDENCE in processing_flags:
                    key_data = self.match_taxon_by_key(taxon.gbif_key)
                    key_usage_key = (
                        (key_data.get('usage') or {}).get('key')
                        if key_data else None
                    )
                    if key_usage_key and str(key_usage_key) == str(taxon.gbif_key):
                        continue
                    if key_usage_key is None:
                        status = 'unresolved'
                        detail = 'Multiple equally-confident name matches; key lookup returned no usage.'
                    else:
                        status = 'stale_key'
                        detail = (
                            'Multiple equally-confident name matches; '
                            'key lookup returned usageKey=%s.' % key_usage_key
                        )
                else:
                    status = 'unresolved'
                    detail = 'GBIF /species/match returned no usage for the name.'
            elif match_type == 'HIGHERRANK':
                matched_name = (data.get('usage') or {}).get('canonicalName') or ''
                if self.names_similar(name, matched_name):
                    # GBIF matched at a higher rank but the name is the same
                    # or close enough - treat the key as still valid.
                    continue
                # Name differs - fall back to a direct key lookup.
                key_data = self.match_taxon_by_key(taxon.gbif_key)
                key_usage_key = (
                    (key_data.get('usage') or {}).get('key')
                    if key_data else None
                )
                if key_usage_key and str(key_usage_key) == str(taxon.gbif_key):
                    continue
                if key_usage_key is None:
                    status = 'unresolved'
                    detail = (
                        'HIGHERRANK match to "%s"; key lookup returned no usage.' % matched_name
                    )
                else:
                    status = 'stale_key'
                    detail = (
                        'HIGHERRANK match to "%s"; key lookup returned usageKey=%s.' % (
                            matched_name, key_usage_key)
                    )
            elif str(current_key) != str(taxon.gbif_key):
                status = 'stale_key'
                detail = 'Current backbone usageKey=%s (matchType=%s).' % (
                    current_key, match_type)
            else:
                continue

            self.stdout.write(self.style.WARNING(
                "  [taxon] %s (gbif_key=%s): %s %s" % (
                    name, taxon.gbif_key, status, detail)))
            findings.append({
                'schema': schema_name,
                'entity': 'taxon',
                'rank': taxon.rank,
                'local_id': taxon.id,
                'name': name,
                'stored_key': taxon.gbif_key,
                'status': status,
                'occurrences': BiologicalCollectionRecord.objects.filter(taxonomy_id=taxon.id).count(),
                'detail': detail,
            })
        return findings

    def match_taxon(self, name):
        """Return the full GBIF v2 /species/match JSON dict, or None on error."""
        try:
            response = self.session.get(
                GBIF_API_V2 + '/species/match',
                params={'scientificName': name, 'strict': True},
                timeout=self.timeout,
            )
            return response.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("match_taxon failed for %s: %s", name, e)
            return None

    def match_taxon_by_key(self, gbif_key):
        """Return the full GBIF v2 /species/match JSON dict looked up by key."""
        try:
            response = self.session.get(
                GBIF_API_V2 + '/species/match',
                params={'usageKey': gbif_key},
                timeout=self.timeout,
            )
            return response.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("match_taxon_by_key failed for %s: %s", gbif_key, e)
            return None

    @staticmethod
    def names_similar(local_name, gbif_name):
        """True if names are the same or one is a prefix of the other (case-insensitive)."""
        a = (local_name or '').strip().lower()
        b = (gbif_name or '').strip().lower()
        if not a or not b:
            return False
        return a == b or a.startswith(b) or b.startswith(a)

    # -------------------------------------------------------------- datasets
    def check_datasets(self, schema_name):
        from bims.models.dataset import Dataset

        qs = Dataset.objects.all().order_by('id')
        if self.limit:
            qs = qs[:self.limit]

        total = qs.count()
        self.stdout.write("  [datasets] checking %d dataset(s)..." % total)
        findings = []
        processed = 0
        for dataset in qs.iterator():
            processed += 1
            self.report_progress('datasets', processed, total, len(findings))
            deleted = self.dataset_deleted(dataset.uuid)
            if not deleted:
                continue
            detail = 'GBIF dataset deleted at %s.' % deleted
            self.stdout.write(self.style.WARNING(
                "  [dataset] %s (%s): %s" % (
                    dataset.name, dataset.uuid, detail)))
            findings.append({
                'schema': schema_name,
                'entity': 'dataset',
                'local_id': dataset.id,
                'name': dataset.name,
                'stored_key': str(dataset.uuid),
                'occurrences': BiologicalCollectionRecord.objects.filter(dataset_key=str(dataset.uuid)).count(),
                'status': 'deleted',
                'detail': detail,
            })
        return findings

    def dataset_deleted(self, uuid):
        """Return the deletion timestamp if the dataset is deleted, else None."""
        try:
            response = self.session.get(
                GBIF_API + '/dataset/%s' % uuid,
                timeout=self.timeout,
            )
            if response.status_code == 404:
                return 'not found (404)'
            data = response.json()
            return data.get('deleted')
        except (requests.RequestException, ValueError) as e:
            logger.warning("dataset_deleted failed for %s: %s", uuid, e)
            return None

    # ----------------------------------------------------------- occurrences
    def check_occurrences(self, schema_name):
        from bims.models.biological_collection_record import (
            BiologicalCollectionRecord,
        )

        qs = BiologicalCollectionRecord.objects.filter(
            source_collection__icontains='gbif',
            upstream_id__isnull=False,
        ).exclude(upstream_id='')

        if self.stale_days:
            cutoff = timezone.now() - timedelta(days=self.stale_days)
            # Never-checked records (modified_date NULL) count as stale.
            qs = qs.filter(
                Q(modified_date__lt=cutoff) | Q(modified_date__isnull=True))

        # Oldest-modified first (NULLs first) so --limit budgets each run to
        # the stalest records and the corpus rotates over successive runs.
        qs = qs.order_by(F('modified_date').asc(nulls_first=True), 'id')

        if self.limit:
            qs = qs[:self.limit]

        total = qs.count()
        self.stdout.write("  [occurrences] checking %d record(s)..." % total)
        findings = []
        processed = 0
        for record in qs.iterator():
            processed += 1
            self.report_progress('occurrences', processed, total, len(findings))
            if not self.occurrence_deleted(record.upstream_id):
                continue
            detail = 'GBIF /occurrence returned 404.'
            self.stdout.write(self.style.WARNING(
                "  [occurrence] record %s (gbifID=%s): deleted" % (
                    record.id, record.upstream_id)))
            findings.append({
                'schema': schema_name,
                'entity': 'occurrence',
                'local_id': record.id,
                'name': record.taxonomy.scientific_name if record.taxonomy else record.original_species_name,
                'stored_key': record.upstream_id,
                'status': 'deleted',
                'modified_date': record.modified_date,
                'detail': detail,
            })
        return findings

    def occurrence_deleted(self, gbif_id):
        """True if GBIF no longer indexes this occurrence (404)."""
        try:
            response = self.session.get(
                GBIF_API + '/occurrence/%s' % gbif_id,
                timeout=self.timeout,
            )
            return response.status_code == 404
        except requests.RequestException as e:
            logger.warning("occurrence_deleted failed for %s: %s", gbif_id, e)
            return False

    # --------------------------------------------------------------- output
    def write_csv(self, path, findings):
        fieldnames = [
            'schema', 'entity', 'rank', 'local_id', 'name',
            'stored_key', 'status', 'occurrences', 'modified_date', 'detail',
        ]
        with open(path, 'w', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(findings)
