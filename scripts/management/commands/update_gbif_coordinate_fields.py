import logging
from decimal import Decimal, InvalidOperation

import requests
from django.core.management import BaseCommand, CommandError
from django.db.models import Q
from django_tenants.utils import get_tenant_model, schema_context
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import RequestException

from bims.models import BiologicalCollectionRecord

GBIF_OCCURRENCE_URL = "https://api.gbif.org/v1/occurrence/{occurrence_id}"
LOG = logging.getLogger(__name__)


def _build_session():
    """Return a requests session with retry semantics for GBIF."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "django-bims coordinate updater"})
    return session


def _to_decimal(value):
    """Convert incoming GBIF numeric values to Decimal or None."""
    if value in (None, "", []):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        value = str(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None


class Command(BaseCommand):
    help = (
        "Fetch coordinatePrecision and coordinateUncertaintyInMeters from "
        "GBIF occurrence API and store them on related LocationSite records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of BiologicalCollectionRecord rows to process per schema (0 = no limit).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch data but do not persist updates.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Update fields even when coordinate values already exist.",
        )
        parser.add_argument(
            "--schema",
            dest="schema",
            help="Tenant schema to process (defaults to current schema).",
        )
        parser.add_argument(
            "--all-tenants",
            dest="all_tenants",
            action="store_true",
            help="Iterate through all tenant schemas (excludes public).",
        )
        parser.add_argument(
            "--print-updates",
            dest="print_updates",
            action="store_true",
            help="Display each updated site (id, upstream id, and fields).",
        )

    def handle(self, *args, **options):
        limit = options.get("limit") or 0
        dry_run = options.get("dry_run", False)
        force = options.get("force", False)
        schema = options.get("schema")
        all_tenants = options.get("all_tenants", False)
        print_updates = options.get("print_updates", False)

        if schema and all_tenants:
            raise CommandError("Use either --schema or --all-tenants, not both.")

        tenant_model = None
        schema_names = []

        if all_tenants:
            tenant_model = get_tenant_model()
            schema_names = list(
                tenant_model.objects.exclude(schema_name="public").values_list(
                    "schema_name", flat=True
                )
            )
            if not schema_names:
                self.stdout.write(self.style.WARNING("No tenant schemas found."))
                return
        elif schema:
            tenant_model = get_tenant_model()
            try:
                tenant_model.objects.get(schema_name=schema)
            except tenant_model.DoesNotExist:
                raise CommandError(f"Tenant schema '{schema}' does not exist.")
            schema_names = [schema]
        else:
            schema_names = [None]

        for schema_name in schema_names:
            if schema_name:
                self.stdout.write(
                    self.style.HTTP_INFO(f"Processing tenant schema '{schema_name}'")
                )
                with schema_context(schema_name):
                    self._process_schema(limit, dry_run, force, print_updates)
            else:
                self.stdout.write(self.style.HTTP_INFO("Processing current schema"))
                self._process_schema(limit, dry_run, force, print_updates)

    def _process_schema(self, limit, dry_run, force, print_updates):
        queryset = (
            BiologicalCollectionRecord.objects.filter(site__isnull=False)
            .exclude(upstream_id__isnull=True)
            .exclude(upstream_id__exact="")
            .filter(
                Q(source_collection__icontains="gbif")
                | Q(site__harvested_from_gbif=True)
            )
            .select_related("site")
            .order_by("pk")
        )

        if not force:
            queryset = queryset.filter(
                Q(site__coordinate_precision__isnull=True)
                | Q(site__coordinate_uncertainty_in_meters__isnull=True)
            )

        total = queryset.count()
        if limit and limit > 0:
            queryset = queryset[:limit]
            total = min(total, limit)

        if total == 0:
            self.stdout.write(self.style.WARNING("No GBIF records require updates."))
            return

        self.stdout.write(
            f"Processing {total} BiologicalCollectionRecord rows"
            f"({'dry-run' if dry_run else 'live'})"
        )

        session = _build_session()
        processed = 0
        updated_sites = 0
        skipped = 0
        errors = 0
        completed_site_ids = set()
        updates_log = []

        try:
            for record in queryset.iterator(chunk_size=200):
                if processed and processed % 10 == 0:
                    self.stdout.write(
                        f"  … processed {processed} records "
                        f"(updates={updated_sites}, skipped={skipped}, errors={errors})"
                    )
                if limit and processed >= limit:
                    break
                processed += 1
                site = record.site
                if not site:
                    skipped += 1
                    continue

                if not force and site.id in completed_site_ids:
                    skipped += 1
                    continue

                upstream_id = (record.upstream_id or "").strip()
                if not upstream_id:
                    skipped += 1
                    continue

                payload = self._fetch_occurrence(session, upstream_id)
                if not payload:
                    errors += 1
                    continue

                coord_precision = _to_decimal(payload.get("coordinatePrecision"))
                coord_uncertainty = _to_decimal(
                    payload.get("coordinateUncertaintyInMeters")
                )

                update_fields = []
                if coord_precision is not None and (
                    force or site.coordinate_precision is None
                ):
                    site.coordinate_precision = coord_precision
                    update_fields.append("coordinate_precision")

                if coord_uncertainty is not None and (
                    force or site.coordinate_uncertainty_in_meters is None
                ):
                    site.coordinate_uncertainty_in_meters = coord_uncertainty
                    update_fields.append("coordinate_uncertainty_in_meters")

                if not site.harvested_from_gbif:
                    site.harvested_from_gbif = True
                    update_fields.append("harvested_from_gbif")

                if update_fields:
                    if not dry_run:
                        site.save(update_fields=update_fields)
                        updates_log.append(
                            {
                                "site_id": site.id,
                                "site_name": site.location_site_identifier,
                                "record_id": record.id,
                                "upstream_id": upstream_id,
                                "fields": list(update_fields),
                            }
                        )
                    updated_sites += 1
                else:
                    skipped += 1

                if (
                    site.coordinate_precision is not None
                    and site.coordinate_uncertainty_in_meters is not None
                ):
                    completed_site_ids.add(site.id)
        finally:
            session.close()

        summary = (
            f"Finished schema. Processed={processed}, updated={updated_sites}, "
            f"skipped={skipped}, errors={errors}"
        )
        if errors:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))

        if print_updates and updates_log:
            self.stdout.write("Updated sites:")
            for entry in updates_log:
                fields = ", ".join(entry["fields"])
                self.stdout.write(
                    f"- site_id={entry['site_id']} name='{entry['site_name']}' "
                    f"(record={entry['record_id']}, upstream={entry['upstream_id']}) "
                    f"fields=[{fields}]"
                )

    def _fetch_occurrence(self, session, upstream_id):
        """Fetch occurrence record from GBIF."""
        url = GBIF_OCCURRENCE_URL.format(occurrence_id=upstream_id)
        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except (RequestException, ValueError) as exc:
            LOG.warning("Failed to fetch GBIF occurrence %s: %s", upstream_id, exc)
            return None
