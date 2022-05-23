import uuid
import logging

from bims.models.survey import Survey

from bims.scripts.collection_csv_keys import *  # noqa
from django.db.models import Q

from bims.models import (
    ChemicalRecord,
    Chem
)
from bims.scripts.occurrences_upload import OccurrenceProcessor
from bims.utils.user import create_users_from_string
from bims.scripts.data_upload import DataCSVUpload
from bims.scripts.collections_upload_source_reference import (
    process_source_reference
)


logger = logging.getLogger('bims')


class PhysicalChemicalProcess(OccurrenceProcessor):

    physico_chemical_units = []
    survey = None

    def chemical_records(
            self, record, location_site, date, source_reference=None):
        """Process chemical data"""
        for chem_key in self.physico_chemical_units:
            chem_value = DataCSVUpload.row_value(record, chem_key).strip()
            if not chem_value:
                continue

            chem = Chem.objects.filter(
                chem_code__iexact=chem_key
            )
            if not chem.exists():
                self.handle_error(
                    row=record,
                    message=(
                        f"Chemical unit {chem_key} doesn't exist in the system"
                    )
                )
                return False

            chem = chem.first()
            chem_record, _ = ChemicalRecord.objects.get_or_create(
                date=date,
                chem=chem,
                location_site=location_site,
                survey=self.survey
            )
            chem_record.value = chem_value
            chem_record.source_reference = source_reference
            chem_record.save()

        return True

    def process_data(self, row):
        # -- Location site
        location_site = self.location_site(row)
        if not location_site:
            return

        # -- UUID
        uuid_value = ''
        # If no uuid provided then it will be generated
        if DataCSVUpload.row_value(row, UUID):
            try:
                test_uuid = (
                    uuid.UUID(DataCSVUpload.row_value(row, UUID)[0:36]).hex
                )
                uuid_value = DataCSVUpload.row_value(row, UUID)
            except ValueError:
                self.handle_error(
                    row=row,
                    message='Bad UUID format'
                )
                return

        uuid_without_hyphen = uuid_value.replace('-', '')

        # -- Source reference
        source = DataCSVUpload.row_value(row, SOURCE)
        source_reference = None
        if source:
            message, source_reference = process_source_reference(
                reference=source,
                reference_category=DataCSVUpload.row_value(
                    row, REFERENCE_CATEGORY),
                doi=DataCSVUpload.row_value(row, DOI),
                document_title=DataCSVUpload.row_value(row, DOCUMENT_TITLE),
                document_link=DataCSVUpload.row_value(row, DOCUMENT_UPLOAD_LINK),
                document_url=DataCSVUpload.row_value(row, DOCUMENT_URL),
                document_author=DataCSVUpload.row_value(row, DOCUMENT_AUTHOR),
                source_year=DataCSVUpload.row_value(row, SOURCE_YEAR)
            )
            if message and not source_reference:
                # Source reference data from csv exists but not created
                self.handle_error(
                    row=row,
                    message=message
                )
                return

        # -- Sampling date
        sampling_date = self.parse_date(row)
        if not sampling_date:
            return

        # -- Processing collectors
        custodian = DataCSVUpload.row_value(row, CUSTODIAN)
        collectors = create_users_from_string(
            DataCSVUpload.row_value(row, COLLECTOR_OR_OWNER))
        if not collectors:
            self.handle_error(
                row=row,
                message='Missing collector/owner'
            )
            return
        if len(collectors) > 0:
            # Add owner and creator to location site
            # if it doesnt exist yet
            if not location_site.owner:
                location_site.owner = collectors[0]
            if not location_site.creator:
                location_site.creator = collectors[0]
            location_site.save()
            if custodian:
                for _collector in collectors:
                    _collector.organization = DataCSVUpload.row_value(
                        row, CUSTODIAN)
                    _collector.save()

        # -- Get or create a survey
        if uuid_value:
            self.survey = Survey.objects.filter(
                Q(uuid=uuid_value) |
                Q(uuid=uuid_without_hyphen)
            ).first()
        if not self.survey:
            self.process_survey(
                row,
                location_site,
                sampling_date,
                collector=collectors[0],
            )

        # -- Processing chemical records
        chemical_record_updated = self.chemical_records(
            row,
            location_site,
            sampling_date,
            source_reference
        )

        if not chemical_record_updated:
            return

        if not str(self.survey.site.id) in self.site_ids:
            self.site_ids.append(
                str(self.survey.site.id)
            )

        self.finish_processing_row(row, self.survey)


class PhysicoChemicalCSVUpload(DataCSVUpload, PhysicalChemicalProcess):
    model_name = 'chemical_record'
    physico_chemical_units = []

    def process_started(self):
        self.start_process()

    def process_ended(self):
        self.finish_process()

    def process_row(self, row):
        self.process_data(row)

    def handle_error(self, row, message):
        self.error_file(
            error_row=row,
            error_message=message
        )

    def finish_processing_row(self, row, record):
        self.success_file(
            success_row=row,
            data_id=record.id
        )
