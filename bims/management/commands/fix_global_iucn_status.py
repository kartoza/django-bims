# coding=utf-8
"""
Tenant-aware command that refreshes the global IUCN Red List status for
every taxon that already has an IUCN taxon id (iucn_redlist_id / sis_id).

For each such taxon it queries the IUCN Red List v4 taxa-by-sis endpoint,
reads the latest assessment's red list category, and updates the taxon's
global ``iucn_status`` (and the ``iucn_data`` url) when it differs.
"""
import time
import logging

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import get_tenant_model, tenant_context

from bims.models.taxonomy import Taxonomy
from bims.utils.iucn import get_iucn_status_by_sis_id, IUCNRateLimitError

logger = logging.getLogger(__name__)

CHUNK_SIZE = 200


class Command(BaseCommand):
    help = (
        "Refresh the global IUCN status of taxa that have an IUCN taxon id "
        "by fetching the latest assessment from the IUCN Red List API."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-s', '--schema-name',
            dest='schema_names',
            action='append',
            help='Tenant schema name(s) to process. Repeatable. Defaults to all tenants.',
        )
        parser.add_argument(
            '-t', '--taxon-id',
            dest='taxon_id',
            type=int,
            default=None,
            help='Only process the taxon with this primary key.',
        )
        parser.add_argument(
            '--limit',
            dest='limit',
            type=int,
            default=None,
            help='Maximum number of taxa to process per tenant.',
        )
        parser.add_argument(
            '--sleep',
            dest='sleep',
            type=float,
            default=1.0,
            help='Seconds to wait between IUCN API calls (default 1.0). '
                 'Increase this if you hit HTTP 429 rate limits.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what would change without writing to the database.',
        )

    def handle(self, *args, **options):
        schema_names = options.get('schema_names') or []
        taxon_id = options.get('taxon_id')
        limit = options.get('limit')
        sleep = options.get('sleep')
        dry_run = options.get('dry_run', False)

        tenants = self._get_tenants(schema_names)
        if not tenants:
            self.stdout.write(self.style.WARNING("No tenants found."))
            return

        mode = "DRY RUN" if dry_run else "LIVE"
        self.stdout.write(f"{mode}: processing {len(tenants)} tenant(s).")

        for tenant in tenants:
            self.stdout.write(
                f"\n── Tenant: {tenant.name} (schema: {tenant.schema_name})"
            )
            with tenant_context(tenant):
                self._process_tenant(
                    taxon_id=taxon_id,
                    limit=limit,
                    sleep=sleep,
                    dry_run=dry_run,
                )

        self.stdout.write(self.style.SUCCESS("\nDone."))

    def _get_tenants(self, schema_names):
        Tenant = get_tenant_model()
        qs = Tenant.objects.exclude(schema_name='public')
        if schema_names:
            qs = qs.filter(schema_name__in=schema_names)
            missing = set(schema_names) - set(
                qs.values_list('schema_name', flat=True)
            )
            if missing:
                raise CommandError(
                    f"Tenant schema(s) not found: {', '.join(sorted(missing))}"
                )
        return list(qs.order_by('schema_name'))

    def _process_tenant(self, taxon_id, limit, sleep, dry_run):
        qs = Taxonomy.objects.filter(
            iucn_redlist_id__isnull=False
        ).select_related('iucn_status').order_by('id')
        if taxon_id:
            qs = qs.filter(pk=taxon_id)

        available = qs.count()
        total = min(available, limit) if limit else available
        self.stdout.write(f"  Taxa with an IUCN taxon id: {total}")
        if total == 0:
            self.stdout.write("  Nothing to process.")
            return

        updated = unchanged = not_found = 0

        # Iterate without slicing so .iterator() stays valid, and stop once
        # the requested limit is reached.
        processed = 0
        for taxon in qs.iterator(chunk_size=CHUNK_SIZE):
            if limit and processed >= limit:
                break
            processed += 1
            sis_id = taxon.iucn_redlist_id
            try:
                iucn_status, _, iucn_url = get_iucn_status_by_sis_id(sis_id)
            except IUCNRateLimitError:
                # Persistent 429 despite retries. Stop so we do not keep
                # hammering the API, and so throttled taxa are not silently
                # recorded as "No status". Rerun (optionally with a larger
                # --sleep) to continue from the remaining taxa.
                self.stdout.write(self.style.ERROR(
                    f"  Aborted at taxon {taxon.id} (sis={sis_id}): IUCN API "
                    f"rate limit. Processed {processed - 1} so far. "
                    f"Rerun with a larger --sleep to continue."
                ))
                break
            if sleep:
                time.sleep(sleep)

            if not iucn_status:
                # No latest global assessment resolvable for this sis id.
                not_found += 1
                logger.info(
                    "No latest global status for taxon %s (sis_id=%s)",
                    taxon.id, sis_id
                )
                continue

            old_status = taxon.iucn_status
            if old_status and old_status.id == iucn_status.id:
                unchanged += 1
                continue

            old_label = old_status.category if old_status else 'None'
            self.stdout.write(
                f"  {'[DRY RUN] ' if dry_run else ''}"
                f"taxon {taxon.id} ({taxon.canonical_name}) "
                f"sis={sis_id}: {old_label} -> {iucn_status.category}"
            )

            if not dry_run:
                fields = {'iucn_status': iucn_status}
                if iucn_url:
                    fields['iucn_data'] = {'url': iucn_url}
                # Bypass Taxonomy post_save so we do not trigger further
                # IUCN look-ups or propagation while backfilling.
                Taxonomy.objects.filter(pk=taxon.pk).update(**fields)

            updated += 1

        summary = (
            f"  Updated: {updated} | Unchanged: {unchanged} | "
            f"No status: {not_found}"
        )
        if dry_run:
            self.stdout.write(summary.replace("Updated", "Would update"))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
