# coding=utf-8
"""
Tenant-aware management command to backfill custodian (institution_id) on
BiologicalCollectionRecord from historical uploaded CSV files.

For older occurrence records, custodian was not stored per occurrence.
Instead the system fell back to the owner's organisation. This command reads
the original process_file CSV from every UploadSession (category='collections'),
matches rows by UUID, and updates institution_id where the CSV carried a
non-empty custodian value that differs from what is stored.
"""

import csv
import logging
from io import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger(__name__)

CUSTODIAN_KEYS = ('Collector/Owner Institute', 'Collector/owner institute')
UUID_KEY = 'UUID'
FALLBACK_ENCODINGS = ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1', 'ISO-8859-1')
INSTITUTION_ID_MAX_LENGTH = 200


class Command(BaseCommand):
    help = (
        'Backfill custodian (institution_id) on BiologicalCollectionRecord '
        'by re-reading the original uploaded CSV files and matching rows by UUID.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-s', '--schema-name',
            dest='schema_names',
            action='append',
            help='Limit to specific tenant schema(s). May be repeated.',
        )
        parser.add_argument(
            '--all-tenants',
            action='store_true',
            help='Process all tenants (default when no --schema-name given).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Report what would change without touching the database (default: True).',
        )
        parser.add_argument(
            '--no-dry-run',
            dest='dry_run',
            action='store_false',
            help='Apply the updates.',
        )
        parser.add_argument(
            '--session-id',
            dest='session_id',
            type=int,
            default=None,
            help='Limit to a specific UploadSession id.',
        )

    def handle(self, *args, **options):
        schema_names = options.get('schema_names') or []
        all_tenants = options.get('all_tenants', False)
        dry_run = options.get('dry_run', True)
        session_id = options.get('session_id')

        if schema_names and all_tenants:
            raise CommandError('Use either --schema-name or --all-tenants, not both.')

        tenants = self._get_tenants(schema_names)
        if not tenants:
            self.stdout.write(self.style.WARNING('No tenants found.'))
            return

        mode = 'DRY RUN' if dry_run else 'LIVE - records will be updated'
        self.stdout.write(f'{mode}: processing {len(tenants)} tenant(s).\n')

        for tenant in tenants:
            self.stdout.write(
                f'-- Tenant: {tenant.name} (schema: {tenant.schema_name})'
            )
            with tenant_context(tenant):
                if dry_run:
                    self._process_tenant(dry_run=True, session_id=session_id)
                else:
                    with transaction.atomic():
                        self._process_tenant(dry_run=False, session_id=session_id)

        self.stdout.write(self.style.SUCCESS('\nDone.'))

    def _get_tenants(self, schema_names):
        Tenant = get_tenant_model()
        qs = Tenant.objects.exclude(schema_name='public')
        if schema_names:
            qs = qs.filter(schema_name__in=schema_names)
            missing = set(schema_names) - set(qs.values_list('schema_name', flat=True))
            if missing:
                raise CommandError(
                    f"Tenant schema(s) not found: {', '.join(sorted(missing))}"
                )
        return list(qs.order_by('schema_name'))

    def _process_tenant(self, dry_run, session_id=None):
        from bims.models.upload_session import UploadSession
        from bims.signals.utils import disconnect_bims_signals, connect_bims_signals

        sessions = UploadSession.objects.filter(
            category='collections',
        ).exclude(process_file='').exclude(process_file__isnull=True)

        if session_id is not None:
            sessions = sessions.filter(id=session_id)

        self.stdout.write(f'  Found {sessions.count()} collection upload session(s).')

        totals = {'updated': 0, 'skipped': 0, 'no_file': 0, 'no_uuid_col': 0}

        disconnect_bims_signals()
        try:
            for session in sessions.iterator():
                try:
                    result = self._process_session(session, dry_run)
                except Exception as exc:
                    logger.warning(
                        'Session %s: unexpected error, skipping session - %s: %s',
                        session.id, type(exc).__name__, exc,
                    )
                    self.stdout.write(
                        f'  Session {session.id}: unexpected error, skipping - {exc}'
                    )
                    totals['no_file'] += 1
                    continue
                for key in totals:
                    totals[key] += result[key]
        finally:
            connect_bims_signals()

        summary = (
            f'  Summary: updated={totals["updated"]}, '
            f'skipped={totals["skipped"]}, '
            f'sessions_without_file={totals["no_file"]}, '
            f'sessions_without_uuid_column={totals["no_uuid_col"]}'
        )
        writer = self.stdout.write
        if dry_run:
            writer(f'  [DRY RUN] {summary}')
        else:
            writer(self.style.SUCCESS(summary))

    def _read_file(self, file_field):
        """Return raw bytes from a FileField, or (None, reason_string)."""
        try:
            path = file_field.path
        except (ValueError, AttributeError):
            return None, 'no local path available'
        try:
            with open(path, 'rb') as fh:
                return fh.read(), None
        except (OSError, IOError) as exc:
            return None, f'could not open file: {exc}'

    def _decode(self, raw):
        """Try multiple encodings and return the first decoded text."""
        for enc in FALLBACK_ENCODINGS:
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return None

    def _normalise_headers(self, fieldnames):
        """Return a dict mapping UPPERCASE_STRIPPED -> original fieldname."""
        return {f.strip().upper(): f.strip() for f in (fieldnames or [])}

    def _process_session(self, session, dry_run):
        result = {'updated': 0, 'skipped': 0, 'no_file': 0, 'no_uuid_col': 0}

        raw, error = self._read_file(session.process_file)
        if raw is None:
            self.stdout.write(f'  Session {session.id}: skipping - {error}')
            result['no_file'] = 1
            return result

        text = self._decode(raw)
        del raw  # free raw bytes; decoded text is all we need now

        if text is None:
            self.stdout.write(
                f'  Session {session.id}: could not decode file, skipping.'
            )
            result['no_file'] = 1
            return result

        reader = csv.DictReader(StringIO(text))
        del text  # StringIO holds its own copy; release the decoded string

        try:
            norm = self._normalise_headers(reader.fieldnames)
        except csv.Error as exc:
            self.stdout.write(
                f'  Session {session.id}: CSV parse error reading headers, skipping - {exc}'
            )
            result['no_file'] = 1
            return result

        uuid_col = norm.get(UUID_KEY.upper())
        if not uuid_col:
            self.stdout.write(
                f'  Session {session.id}: no UUID column found, skipping.'
            )
            result['no_uuid_col'] = 1
            return result

        custodian_col = next(
            (norm[k.upper()] for k in CUSTODIAN_KEYS if k.upper() in norm),
            None,
        )
        if not custodian_col:
            self.stdout.write(
                f'  Session {session.id}: no custodian column found, skipping.'
            )
            return result

        from bims.models.biological_collection_record import BiologicalCollectionRecord

        try:
            for row in reader:  # stream one row at a time; no full list in memory
                uuid_val = (row.get(uuid_col) or '').strip()
                custodian = (row.get(custodian_col) or '').strip()

                if not uuid_val or not custodian or custodian == '-':
                    result['skipped'] += 1
                    continue

                if len(custodian) > INSTITUTION_ID_MAX_LENGTH:
                    self.stdout.write(
                        f'  Session {session.id}: UUID={uuid_val}: custodian value '
                        f'exceeds {INSTITUTION_ID_MAX_LENGTH} chars, skipping row.'
                    )
                    result['skipped'] += 1
                    continue

                try:
                    record = BiologicalCollectionRecord.objects.get(uuid=uuid_val)
                except BiologicalCollectionRecord.DoesNotExist:
                    result['skipped'] += 1
                    continue
                except BiologicalCollectionRecord.MultipleObjectsReturned:
                    self.stdout.write(
                        f'  Session {session.id}: multiple records for UUID {uuid_val}, skipping row.'
                    )
                    result['skipped'] += 1
                    continue
                except Exception as exc:
                    logger.warning(
                        'Session %s: unexpected error looking up UUID %s: %s',
                        session.id, uuid_val, exc,
                    )
                    result['skipped'] += 1
                    continue

                if record.institution_id == custodian:
                    result['skipped'] += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        f'  [DRY RUN] UUID={uuid_val}: '
                        f'institution_id "{record.institution_id}" -> "{custodian}"'
                    )
                else:
                    record.institution_id = custodian
                    record.save(update_fields=['institution_id'])

                result['updated'] += 1

        except csv.Error as exc:
            self.stdout.write(
                f'  Session {session.id}: CSV parse error at line {reader.line_num}, '
                f'skipping remaining rows - {exc}'
            )

        return result
