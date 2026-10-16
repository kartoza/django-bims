# coding=utf-8
"""
Export the occurrence records with a missing or doubtful Collector/Owner,
with a possible owner.

When no owner was given the system deferred to the uploader, so the owner of
many records is the uploader (or blank, or a generic admin account). The
records exported are:

  owner_blank                       owner is empty
  owner_is_admin                    owner is an admin account (kartoza_admin)
  session_csv_blank_owner           the owner is the uploader of the upload
                                    session, and the Collector/Owner of the
                                    uploaded file was blank for the record
  owner_is_uploader_collector_blank the owner is the uploader and the
                                    collector of the record is blank (no
                                    upload file to prove it)

possible_owner is the best evidence for who the owner should be, in order:

  collector_text          the collector text of the record is exactly one
                          user (username or full name)
  sass_site_visit         SASS data only: the owner of the site visit of the
                          record (not the current owner or an admin)
  same_survey             the other records of the same survey agree on one
                          owner (not the uploader or an admin)
  source_reference_author the source reference has exactly one author that
                          is a registered user
  uploader                the uploader, only for admin owned records
  none                    nothing found

Nothing is written to the database.

    python manage.py export_owner_candidates -s fbis -o owners_fbis.csv \
        --domain freshwaterbiodiversity.org
"""
import csv
import logging
import os
from collections import defaultdict
from io import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Exists, F, OuterRef, Q, Subquery
from django.db.models.functions import Lower
from django_tenants.utils import get_tenant_model, tenant_context

from bims.management.commands.export_legacy_custodian_candidates import (
    EXCLUDED_SOURCE_COLLECTIONS, Command as CustodianExport, base_url,
    record_path
)

logger = logging.getLogger(__name__)

COLLECTOR_KEYS = ('COLLECTOR/OWNER',)
UUID_KEY = 'UUID'
ENCODINGS = ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1')
CHUNK = 5000

CONFIDENCE = {
    'collector_text': 'high',
    'sass_site_visit': 'medium',
    'same_survey': 'medium',
    'source_reference_author': 'medium',
    'uploader': 'low',
    'none': '',
}

CSV_FIELDS = [
    'uuid', 'id', 'record_url', 'is_sass', 'collection_date',
    'original_species_name', 'site_code', 'site_name',
    'current_owner', 'current_owner_name', 'uploader', 'collector_text',
    'source_reference_id', 'source_reference', 'reason',
    'possible_owner', 'possible_owner_name', 'possible_owner_source',
    'confidence', 'evidence',
    # filled in by the reviewer
    'action', 'final_owner',
]


def is_admin(username):
    return 'admin' in (username or '').lower()


def reason_for(row, blank_in_session):
    """Why a record is exported, or '' when it is fine."""
    owner_id = row['owner_id']
    if owner_id is None:
        return 'owner_blank'
    if is_admin(row['owner__username']):
        return 'owner_is_admin'
    uploader_id = row['collector_user_id']
    if owner_id != uploader_id:
        return ''
    if row['uuid'] in blank_in_session:
        return 'session_csv_blank_owner'
    if not (row['collector'] or '').strip():
        return 'owner_is_uploader_collector_blank'
    return ''


def choose_owner(row, users, by_survey, by_reference, site_visit_owners=None):
    """Return (user_id, source, evidence) of a possible owner."""
    current = row['owner_id']
    uploader = row['collector_user_id']

    text = (row['collector'] or '').strip().lower()
    if text:
        matches = users['by_name'].get(text, set())
        matches = {m for m in matches if m != current}
        if len(matches) == 1:
            return next(iter(matches)), 'collector_text', (
                f'collector text "{row["collector"].strip()}"')

    if row.get('is_sass') and site_visit_owners:
        visit_owner = site_visit_owners.get(row.get('sass_site_visit_id'))
        if (visit_owner and visit_owner not in (current, uploader)
                and not is_admin(users['username'].get(visit_owner, ''))):
            return visit_owner, 'sass_site_visit', (
                'owner of the SASS site visit')

    survey_owners = {
        owner for owner in by_survey.get(row['survey_id'], set())
        if owner not in (current, uploader)
    }
    if len(survey_owners) == 1:
        return next(iter(survey_owners)), 'same_survey', (
            'owner of the other records of the same survey')

    authors = {
        user for user in by_reference.get(row['source_reference_id'], set())
        if user != current
    }
    if len(authors) == 1:
        return next(iter(authors)), 'source_reference_author', (
            'only registered author of the source reference')

    if (is_admin(row['owner__username']) and uploader
            and uploader != current
            and not is_admin(users['username'].get(uploader, ''))):
        return uploader, 'uploader', 'uploader of the record'
    return None, 'none', ''


class Command(BaseCommand):
    help = (
        'Export occurrences with a blank, admin or uploader owner with a '
        'possible owner, to be checked before apply_owner_candidates.'
    )

    def add_arguments(self, parser):
        parser.add_argument('-s', '--schema-name', required=True)
        parser.add_argument('-o', '--output', default=None)
        parser.add_argument(
            '--domain', default='',
            help='Domain of the site, e.g. freshwaterbiodiversity.org, used '
                 'for the record_url column')
        parser.add_argument(
            '--skip-sessions', action='store_true',
            help='Do not read the uploaded files of the upload sessions '
                 '(faster, only the collector text is used as evidence)')

    def handle(self, *args, **options):
        schema = options['schema_name']
        output = options['output'] or f'owner_candidates_{schema}.csv'
        try:
            tenant = get_tenant_model().objects.get(schema_name=schema)
        except get_tenant_model().DoesNotExist:
            raise CommandError(f'Tenant "{schema}" not found.')
        with tenant_context(tenant):
            self.export(
                output, base_url(options['domain']),
                not options['skip_sessions'])

    # -- upload sessions ---------------------------------------------------

    def blank_owner_uuids(self):
        """UUIDs of the records whose Collector/Owner was blank in the
        uploaded file."""
        from bims.models.upload_session import UploadSession

        blank = set()
        sessions = UploadSession.objects.filter(
            category='collections'
        ).exclude(process_file='').exclude(process_file__isnull=True)
        for session in sessions.iterator():
            try:
                with open(session.process_file.path, 'rb') as handle:
                    raw = handle.read()
            except (ValueError, OSError):
                continue
            text = None
            for encoding in ENCODINGS:
                try:
                    text = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            del raw
            if text is None:
                continue
            reader = csv.DictReader(StringIO(text, newline=''))
            del text
            try:
                names = {
                    (f or '').strip().upper(): f
                    for f in (reader.fieldnames or [])
                }
                uuid_col = names.get(UUID_KEY)
                owner_col = next(
                    (names[k] for k in COLLECTOR_KEYS if k in names), None)
                if not uuid_col or not owner_col:
                    continue
                for row in reader:
                    value = (row.get(uuid_col) or '').strip()
                    if value and not (row.get(owner_col) or '').strip():
                        blank.add(value)
            except csv.Error as exc:
                logger.warning(
                    'Session %s: CSV error, skipped - %s', session.id, exc)
        return blank

    # -- export ------------------------------------------------------------

    def export(self, output, domain, use_sessions):
        from django.contrib.auth import get_user_model
        from bims.models.biological_collection_record import (
            BiologicalCollectionRecord
        )
        from bims.models.source_reference import SourceReferenceAuthor
        from sass.models.site_visit import SiteVisit
        from sass.models.site_visit_taxon import SiteVisitTaxon

        blank_uuids = self.blank_owner_uuids() if use_sessions else set()
        self.stdout.write(
            f'Records with a blank Collector/Owner in an uploaded file: '
            f'{len(blank_uuids)}')

        base = BiologicalCollectionRecord.objects.exclude(
            source_collection__in=EXCLUDED_SOURCE_COLLECTIONS)
        blank_collector = Q(collector='') | Q(collector__isnull=True)
        candidates = base.filter(
            Q(owner__isnull=True) |
            Q(owner__username__icontains='admin') |
            (Q(owner_id=F('collector_user_id')) & blank_collector)
        )
        ids = set(candidates.values_list('id', flat=True))
        # records proven by the uploaded files
        pending = list(blank_uuids)
        for start in range(0, len(pending), CHUNK):
            ids.update(base.filter(
                uuid__in=pending[start:start + CHUNK],
                owner_id=F('collector_user_id')
            ).values_list('id', flat=True))
        self.stdout.write(f'Records to check: {len(ids)}')
        if not ids:
            return

        # Users, by username and by full name
        User = get_user_model()
        users = {'by_name': defaultdict(set), 'username': {}, 'name': {}}
        for user_id, username, first, last in User.objects.values_list(
            'id', 'username', 'first_name', 'last_name'
        ):
            full = f'{first} {last}'.strip()
            users['username'][user_id] = username
            users['name'][user_id] = full
            users['by_name'][username.lower()].add(user_id)
            if full:
                users['by_name'][full.lower()].add(user_id)

        selected = base.filter(id__in=ids)
        survey_ids = set(selected.exclude(
            survey_id__isnull=True).values_list('survey_id', flat=True))
        reference_ids = set(selected.exclude(
            source_reference_id__isnull=True
        ).values_list('source_reference_id', flat=True))

        site_visit_owners = dict(SiteVisit.objects.filter(
            id__in=SiteVisitTaxon.objects.filter(
                id__in=ids).values('site_visit_id'),
            owner__isnull=False
        ).values_list('id', 'owner_id'))

        by_survey = defaultdict(set)
        for survey_id, owner_id in base.filter(
            survey_id__in=survey_ids, owner__isnull=False
        ).exclude(owner__username__icontains='admin').values_list(
            'survey_id', 'owner_id'
        ).distinct():
            by_survey[survey_id].add(owner_id)

        by_reference = defaultdict(set)
        for reference_id, user_id in SourceReferenceAuthor.objects.filter(
            source_reference_id__in=reference_ids,
            author__user__isnull=False
        ).values_list('source_reference_id', 'author__user_id'):
            by_reference[reference_id].add(user_id)

        titles = CustodianExport.reference_titles(reference_ids)

        rows = selected.annotate(
            is_sass=Exists(
                SiteVisitTaxon.objects.filter(pk=OuterRef('pk'))),
            sass_site_visit_id=Subquery(
                SiteVisitTaxon.objects.filter(
                    pk=OuterRef('pk')).values('site_visit_id')[:1]),
        ).values(
            'uuid', 'id', 'is_sass', 'sass_site_visit_id', 'survey_id',
            'collection_date', 'original_species_name', 'site__site_code',
            'site__name', 'owner_id', 'owner__username', 'collector_user_id',
            'collector', 'source_reference_id',
        ).order_by('source_reference_id', 'site_id', 'id')

        summary = defaultdict(int)
        written = 0
        with open(output, 'w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for row in rows.iterator(chunk_size=2000):
                row['uuid'] = str(row['uuid'])
                reason = reason_for(row, blank_uuids)
                if not reason:
                    continue
                owner_id, source, evidence = choose_owner(
                    row, users, by_survey, by_reference,
                    site_visit_owners)
                summary[(reason, source)] += 1
                path = record_path(
                    row['is_sass'], row['sass_site_visit_id'],
                    row['survey_id'])
                writer.writerow({
                    'uuid': row['uuid'],
                    'id': f'{domain}/admin/bims/biologicalcollectionrecord/{row['id']}',
                    'record_url': f'{domain}{path}' if path else '',
                    'is_sass': 'yes' if row['is_sass'] else 'no',
                    'collection_date': row['collection_date'] or '',
                    'original_species_name': row['original_species_name'],
                    'site_code': row['site__site_code'] or '',
                    'site_name': row['site__name'] or '',
                    'current_owner': row['owner__username'] or '',
                    'current_owner_name': users['name'].get(
                        row['owner_id'], ''),
                    'uploader': users['username'].get(
                        row['collector_user_id'], ''),
                    'collector_text': (row['collector'] or '').strip(),
                    'source_reference_id': row['source_reference_id'] or '',
                    'source_reference': titles.get(
                        row['source_reference_id'], ''),
                    'reason': reason,
                    'possible_owner': users['username'].get(owner_id, ''),
                    'possible_owner_name': users['name'].get(owner_id, ''),
                    'possible_owner_source': source,
                    'confidence': CONFIDENCE[source],
                    'evidence': evidence,
                    'action': '',
                    'final_owner': '',
                })
                written += 1

        self.stdout.write(self.style.SUCCESS(
            f'Wrote {written} rows to {os.path.abspath(output)}'))
        self.stdout.write('Reason / possible owner source: records')
        for (reason, source), count in sorted(summary.items()):
            self.stdout.write(f'  {reason:36} {source:24} {count}')
