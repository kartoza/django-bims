# coding=utf-8
import io
import shutil
import tempfile
import uuid

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase

from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    UploadSessionF,
)

MEDIA_ROOT = tempfile.mkdtemp()

# Real-world BIMS collection CSV column headers
_HEADERS = [
    'UUID',
    'Taxon',
    'Taxon rank',
    'Latitude',
    'Longitude',
    'Sampling Date',
    'Collector/Owner',
    'Collector/Owner Institute',
]


def _make_csv(rows):
    """Return a CSV string using real BIMS column headers."""
    lines = [','.join(_HEADERS)]
    for row in rows:
        lines.append(','.join([
            row.get('UUID', ''),
            row.get('Taxon', 'Rana temporaria'),
            row.get('Taxon rank', 'Species'),
            row.get('Latitude', '-26.2041'),
            row.get('Longitude', '28.0473'),
            row.get('Sampling Date', '2020-01-15'),
            row.get('Collector/Owner', 'John Doe'),
            row.get('Collector/Owner Institute', ''),
        ]))
    return '\n'.join(lines)


def _make_session(csv_content, name='test.csv'):
    """Create a collections UploadSession with csv_content as its process_file."""
    session = UploadSessionF.create(category='collections')
    session.process_file.save(name, ContentFile(csv_content.encode('utf-8')))
    return session


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TestBackfillCustodian(FastTenantTestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.site = LocationSiteF.create()
        self.schema = self.tenant.schema_name

    def _call(self, dry_run=False, **kwargs):
        """Convenience wrapper that always targets the test tenant."""
        out = io.StringIO()
        call_command(
            'backfill_custodian',
            schema_names=[self.schema],
            dry_run=dry_run,
            stdout=out,
            **kwargs,
        )
        return out.getvalue()

    # ------------------------------------------------------------------
    # Core update behaviour
    # ------------------------------------------------------------------

    def test_updates_institution_id_from_csv(self):
        record_uuid = str(uuid.uuid4())
        record = BiologicalCollectionRecordF.create(
            site=self.site,
            uuid=record_uuid,
            institution_id='Wrong Institution',
        )
        _make_session(_make_csv([{
            'UUID': record_uuid,
            'Collector/Owner Institute': 'South African Institute for Aquatic Biodiversity',
        }]))

        self._call()

        record.refresh_from_db()
        self.assertEqual(
            record.institution_id,
            'South African Institute for Aquatic Biodiversity',
        )

    def test_processes_multiple_records_from_single_session(self):
        uuids = [str(uuid.uuid4()) for _ in range(3)]
        records = [
            BiologicalCollectionRecordF.create(
                site=self.site,
                uuid=uuids[i],
                institution_id='Old Institute',
            )
            for i in range(3)
        ]
        _make_session(_make_csv([
            {'UUID': uuids[0], 'Collector/Owner Institute': 'Institute A'},
            {'UUID': uuids[1], 'Collector/Owner Institute': 'Institute B'},
            {'UUID': uuids[2], 'Collector/Owner Institute': 'Institute C'},
        ]))

        self._call()

        for i, record in enumerate(records):
            record.refresh_from_db()
            self.assertEqual(record.institution_id, f'Institute {chr(65 + i)}')

    def test_processes_multiple_sessions(self):
        """Records across multiple upload sessions are all updated in one run."""
        # Session 1: field survey upload (2 records)
        uuid_s1_a, uuid_s1_b = str(uuid.uuid4()), str(uuid.uuid4())
        rec_s1_a = BiologicalCollectionRecordF.create(
            site=self.site, uuid=uuid_s1_a, institution_id='Wrong'
        )
        rec_s1_b = BiologicalCollectionRecordF.create(
            site=self.site, uuid=uuid_s1_b, institution_id='Wrong'
        )
        _make_session(_make_csv([
            {'UUID': uuid_s1_a, 'Collector/Owner Institute': 'SAEON'},
            {'UUID': uuid_s1_b, 'Collector/Owner Institute': 'SAEON'},
        ]), name='survey_2019.csv')

        # Session 2: museum specimen import (1 record)
        uuid_s2_a = str(uuid.uuid4())
        rec_s2_a = BiologicalCollectionRecordF.create(
            site=self.site, uuid=uuid_s2_a, institution_id='Wrong'
        )
        _make_session(_make_csv([
            {'UUID': uuid_s2_a, 'Collector/Owner Institute': 'South African Museum'},
        ]), name='museum_2020.csv')

        # Session 3: citizen science upload; one row has '-' custodian and must be skipped
        uuid_s3_a, uuid_s3_b = str(uuid.uuid4()), str(uuid.uuid4())
        rec_s3_a = BiologicalCollectionRecordF.create(
            site=self.site, uuid=uuid_s3_a, institution_id='Wrong'
        )
        rec_s3_b = BiologicalCollectionRecordF.create(
            site=self.site, uuid=uuid_s3_b, institution_id='Original'
        )
        _make_session(_make_csv([
            {'UUID': uuid_s3_a, 'Collector/Owner Institute': 'iNaturalist'},
            {'UUID': uuid_s3_b, 'Collector/Owner Institute': '-'},
        ]), name='citizen_2021.csv')

        output = self._call()

        rec_s1_a.refresh_from_db()
        rec_s1_b.refresh_from_db()
        rec_s2_a.refresh_from_db()
        rec_s3_a.refresh_from_db()
        rec_s3_b.refresh_from_db()

        self.assertEqual(rec_s1_a.institution_id, 'SAEON')
        self.assertEqual(rec_s1_b.institution_id, 'SAEON')
        self.assertEqual(rec_s2_a.institution_id, 'South African Museum')
        self.assertEqual(rec_s3_a.institution_id, 'iNaturalist')
        self.assertEqual(rec_s3_b.institution_id, 'Original')  # '-' custodian skipped
        self.assertIn('updated=4', output)
        self.assertIn('skipped=1', output)

    def test_uses_lowercase_custodian_column_variant(self):
        """'Collector/owner institute' (lowercase o/i) must also be recognised."""
        record_uuid = str(uuid.uuid4())
        record = BiologicalCollectionRecordF.create(
            site=self.site,
            uuid=record_uuid,
            institution_id='Old',
        )
        csv_content = (
            'UUID,Taxon,Taxon rank,Latitude,Longitude,'
            'Sampling Date,Collector/Owner,Collector/owner institute\n'
            f'{record_uuid},Rana temporaria,Species,'
            '-26.2041,28.0473,2020-01-15,Jane Smith,iNaturalist South Africa\n'
        )
        session = UploadSessionF.create(category='collections')
        session.process_file.save('lower.csv', ContentFile(csv_content.encode('utf-8')))

        self._call()

        record.refresh_from_db()
        self.assertEqual(record.institution_id, 'iNaturalist South Africa')

    # ------------------------------------------------------------------
    # Dry-run behaviour
    # ------------------------------------------------------------------

    def test_dry_run_does_not_update_record(self):
        record_uuid = str(uuid.uuid4())
        record = BiologicalCollectionRecordF.create(
            site=self.site,
            uuid=record_uuid,
            institution_id='Old Institution',
        )
        _make_session(_make_csv([{
            'UUID': record_uuid,
            'Collector/Owner Institute': 'New Institution',
        }]))

        output = self._call(dry_run=True)

        record.refresh_from_db()
        self.assertEqual(record.institution_id, 'Old Institution')
        self.assertIn('[DRY RUN]', output)

    # ------------------------------------------------------------------
    # Skip conditions
    # ------------------------------------------------------------------

    def test_skips_row_when_institution_id_already_matches(self):
        record_uuid = str(uuid.uuid4())
        record = BiologicalCollectionRecordF.create(
            site=self.site,
            uuid=record_uuid,
            institution_id='Correct Institution',
        )
        _make_session(_make_csv([{
            'UUID': record_uuid,
            'Collector/Owner Institute': 'Correct Institution',
        }]))

        self._call()

        record.refresh_from_db()
        self.assertEqual(record.institution_id, 'Correct Institution')

    def test_skips_row_with_dash_custodian(self):
        record_uuid = str(uuid.uuid4())
        record = BiologicalCollectionRecordF.create(
            site=self.site,
            uuid=record_uuid,
            institution_id='Original Institution',
        )
        _make_session(_make_csv([{
            'UUID': record_uuid,
            'Collector/Owner Institute': '-',
        }]))

        self._call()

        record.refresh_from_db()
        self.assertEqual(record.institution_id, 'Original Institution')

    def test_skips_row_with_empty_custodian(self):
        record_uuid = str(uuid.uuid4())
        record = BiologicalCollectionRecordF.create(
            site=self.site,
            uuid=record_uuid,
            institution_id='Original Institution',
        )
        _make_session(_make_csv([{
            'UUID': record_uuid,
            'Collector/Owner Institute': '',
        }]))

        self._call()

        record.refresh_from_db()
        self.assertEqual(record.institution_id, 'Original Institution')

    def test_skips_row_with_empty_uuid(self):
        record = BiologicalCollectionRecordF.create(
            site=self.site,
            institution_id='Original Institution',
        )
        _make_session(_make_csv([{
            'UUID': '',
            'Collector/Owner Institute': 'New Institution',
        }]))

        self._call()

        record.refresh_from_db()
        self.assertEqual(record.institution_id, 'Original Institution')

    def test_skips_row_with_unknown_uuid(self):
        """A UUID that has no matching record must not raise and must be skipped."""
        _make_session(_make_csv([{
            'UUID': str(uuid.uuid4()),
            'Collector/Owner Institute': 'Some Institute',
        }]))

        output = self._call()

        self.assertIn('skipped=1', output)

    # ------------------------------------------------------------------
    # Session-level skip conditions
    # ------------------------------------------------------------------

    def test_handles_session_with_missing_file_on_disk(self):
        session = UploadSessionF.create(category='collections')
        session.process_file.name = 'taxa-file/does_not_exist.csv'
        session.save(update_fields=['process_file'])

        output = self._call()

        self.assertIn('skipping', output.lower())

    def test_handles_csv_without_uuid_column(self):
        csv_no_uuid = (
            'Taxon,Taxon rank,Collector/Owner Institute\n'
            'Bufo bufo,Species,South African Institute for Aquatic Biodiversity\n'
        )
        session = UploadSessionF.create(category='collections')
        session.process_file.save('no_uuid.csv', ContentFile(csv_no_uuid.encode('utf-8')))

        output = self._call()

        self.assertIn('no UUID column', output)

    def test_handles_csv_without_custodian_column(self):
        csv_no_cust = (
            'UUID,Taxon,Taxon rank\n'
            f'{uuid.uuid4()},Bufo bufo,Species\n'
        )
        session = UploadSessionF.create(category='collections')
        session.process_file.save('no_cust.csv', ContentFile(csv_no_cust.encode('utf-8')))

        output = self._call()

        self.assertIn('no custodian column', output)

    # ------------------------------------------------------------------
    # Session filter
    # ------------------------------------------------------------------

    def test_session_id_limits_to_single_session(self):
        uuid_a = str(uuid.uuid4())
        uuid_b = str(uuid.uuid4())

        record_a = BiologicalCollectionRecordF.create(
            site=self.site, uuid=uuid_a, institution_id='Old'
        )
        record_b = BiologicalCollectionRecordF.create(
            site=self.site, uuid=uuid_b, institution_id='Old'
        )

        session_a = _make_session(_make_csv([
            {'UUID': uuid_a, 'Collector/Owner Institute': 'Institute A'},
        ]), name='session_a.csv')
        _make_session(_make_csv([
            {'UUID': uuid_b, 'Collector/Owner Institute': 'Institute B'},
        ]), name='session_b.csv')

        self._call(session_id=session_a.id)

        record_a.refresh_from_db()
        record_b.refresh_from_db()
        self.assertEqual(record_a.institution_id, 'Institute A')
        self.assertEqual(record_b.institution_id, 'Old')
