import uuid
import json
import logging
from bims.scripts.collection_csv_keys import *  # noqa
from datetime import datetime

from django.contrib.gis.geos import Point
from django.db.models import Q, signals

from bims.models import (
    LocationType,
    LocationSite,
    Endemism,
    BiologicalCollectionRecord,
    SamplingMethod,
    Taxonomy,
    SourceReference,
    ChemicalRecord,
    Chem,
    Biotope,
    BIOTOPE_TYPE_BROAD,
    BIOTOPE_TYPE_SPECIFIC,
    BIOTOPE_TYPE_SUBSTRATUM,
    location_site_post_save_handler,
    collection_post_save_handler,
    SourceReferenceBibliography,
    Survey,
    SurveyData,
    SurveyDataOption,
    SurveyDataValue,
    LocationContextGroup,
    LocationContextFilter,
    LocationContextFilterGroupOrder,
    source_reference_post_save_handler,
    SourceReferenceDatabase,
    SourceReferenceDocument,
    location_context_post_save_handler
)
from bims.utils.user import create_users_from_string
from bims.scripts.data_upload import DataCSVUpload
from bims.tasks.location_site import update_location_context
from bims.scripts.collections_upload_source_reference import (
    process_source_reference
)
from bims.tasks.location_context import generate_spatial_scale_filter
from bims.tasks.source_reference import (
    generate_source_reference_filter
)
from bims.models.location_site import generate_site_code


logger = logging.getLogger('bims')


class OccurrenceProcessor(object):

    site_ids = []
    module_group = None
    # Whether the script should also fetch location context after ingesting
    # collection data
    fetch_location_context = True

    def start_process(self):
        signals.post_save.disconnect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
        signals.post_save.disconnect(
            location_site_post_save_handler,
            sender=LocationSite
        )
        signals.post_save.disconnect(
            source_reference_post_save_handler,
            sender=SourceReference
        )
        signals.post_save.disconnect(
            source_reference_post_save_handler,
            sender=SourceReferenceDatabase
        )
        signals.post_save.disconnect(
            source_reference_post_save_handler,
            sender=SourceReferenceBibliography
        )
        signals.post_save.disconnect(
            source_reference_post_save_handler,
            sender=SourceReferenceDocument
        )
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextGroup
        )
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextFilter
        )
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextFilterGroupOrder
        )

    def finish_process(self):
        if self.site_ids and self.fetch_location_context:
            update_location_context.delay(
                location_site_id=','.join(self.site_ids),
                generate_site_code=True
            )
        signals.post_save.connect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
        signals.post_save.connect(
            location_site_post_save_handler,
            sender=LocationSite
        )
        signals.post_save.connect(
            source_reference_post_save_handler,
            sender=SourceReference
        )
        signals.post_save.connect(
            source_reference_post_save_handler,
            sender=SourceReferenceDatabase
        )
        signals.post_save.connect(
            source_reference_post_save_handler,
            sender=SourceReferenceBibliography
        )
        signals.post_save.connect(
            source_reference_post_save_handler,
            sender=SourceReferenceDocument
        )
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextGroup
        )
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextFilter
        )
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextFilterGroupOrder
        )
        generate_spatial_scale_filter()
        # Update source reference filter
        generate_source_reference_filter()

    def handle_error(self, row, message):
        pass

    def finish_processing_row(self, row, record):
        pass

    def parse_date(self, row):
        # Parse date string to date object
        # Raise value error if date string is not in a valid format
        sampling_date = None
        date_string = DataCSVUpload.row_value(row, SAMPLING_DATE)
        try:
            sampling_date = datetime.strptime(
                date_string, '%Y/%m/%d')
        except ValueError:
            sampling_date = datetime.strptime(
                date_string, '%m/%d/%Y')
        finally:
            if not sampling_date:
                self.handle_error(
                    row=row,
                    message='Incorrect date format'
                )
            return sampling_date

    def process_survey(self, record, location_site, sampling_date, collector):
        """Process survey data"""
        try:
            self.survey, _ = Survey.objects.get_or_create(
                site=location_site,
                date=sampling_date,
                collector_user=collector,
                owner=collector
            )
        except Survey.MultipleObjectsReturned:
            self.survey = Survey.objects.get_or_create(
                site=location_site,
                date=sampling_date,
                collector_user=collector,
                owner=collector
            )[0]

        for survey_data_key in SURVEY_DATA:
            if survey_data_key in record and DataCSVUpload.row_value(
                    record,
                    survey_data_key):
                survey_data, _ = SurveyData.objects.get_or_create(
                    name=SURVEY_DATA[survey_data_key]
                )
                survey_option = SurveyDataOption.objects.filter(
                    option__iexact=DataCSVUpload.row_value(
                        record,
                        survey_data_key).strip(),
                    survey_data=survey_data
                )
                if not survey_option.exists():
                    survey_option = SurveyDataOption.objects.create(
                        options=DataCSVUpload.row_value(
                            record,
                            survey_data_key).strip(),
                        survey_data=survey_data
                    )
                else:
                    survey_option = survey_option[0]
                if survey_option:
                    SurveyDataValue.objects.get_or_create(
                        survey=self.survey,
                        survey_data=survey_data,
                        survey_data_option=survey_option,
                    )

    def location_site(self, record):
        """ Process location site data """
        location_site = None
        location_type, status = LocationType.objects.get_or_create(
            name='PointObservation',
            allowed_geometry='POINT'
        )
        site_description = DataCSVUpload.row_value(record, SITE_DESCRIPTION)
        refined_geo = DataCSVUpload.row_value(record, REFINED_GEO_ZONE)
        legacy_river_name = DataCSVUpload.row_value(
            record, ORIGINAL_RIVER_NAME)
        longitude = DataCSVUpload.row_value(record, LONGITUDE)
        latitude = DataCSVUpload.row_value(record, LATITUDE)
        if not longitude or not latitude:
            self.handle_error(
                row=record,
                message='Missing latitude/longitude'
            )
            return None

        latitude = float(DataCSVUpload.row_value(record, LATITUDE))
        longitude = float(DataCSVUpload.row_value(record, LONGITUDE))
        record_point = Point(
            longitude,
            latitude)
        # Create or get location site
        legacy_site_code = DataCSVUpload.row_value(record, ORIGINAL_SITE_CODE)
        location_site_name = ''
        if DataCSVUpload.row_value(record, LOCATION_SITE):
            location_site_name = DataCSVUpload.row_value(record, LOCATION_SITE)
        elif DataCSVUpload.row_value(record, WETLAND_NAME):
            location_site_name = DataCSVUpload.row_value(record, WETLAND_NAME)

        # Find existing location site by FBIS site code
        fbis_site_code = DataCSVUpload.row_value(record, FBIS_SITE_CODE)
        if fbis_site_code:
            location_site = LocationSite.objects.filter(
                site_code__iexact=fbis_site_code.strip()
            ).first()

        # Find existing location site by lat and lon
        if len(str(latitude)) > 5 and len(str(longitude)) > 5:
            location_site = LocationSite.objects.filter(
                latitude__startswith=latitude,
                longitude__startswith=longitude
            ).first()

        if not location_site:
            try:
                location_site, status = (
                    LocationSite.objects.get_or_create(
                        location_type=location_type,
                        geometry_point=record_point
                    )
                )
            except LocationSite.MultipleObjectsReturned:
                location_site = LocationSite.objects.filter(
                    location_type=location_type,
                    geometry_point=record_point
                ).first()
        if not location_site.name and location_site_name:
            location_site.name = location_site_name
        if not location_site.legacy_site_code and legacy_site_code:
            location_site.legacy_site_code = legacy_site_code
        if not location_site.site_description and site_description:
            location_site.site_description = site_description
        if refined_geo:
            location_site.refined_geomorphological = refined_geo
        if legacy_river_name:
            location_site.legacy_river_name = legacy_river_name
        if not location_site.site_code:
            site_code, catchments_data = generate_site_code(
                location_site,
                lat=location_site.latitude,
                lon=location_site.longitude
            )
            location_site.site_code = site_code
        location_site.save()
        return location_site

    def biotope(self, record, biotope_record_type, biotope_type):
        """Process biotope data"""
        biotope = None
        if (
                DataCSVUpload.row_value(record, biotope_record_type) and
                DataCSVUpload.row_value(
                    record, biotope_record_type).lower() != 'unspecified'):
            try:
                biotope, biotope_created = (
                    Biotope.objects.get_or_create(
                        biotope_type=biotope_type,
                        name=DataCSVUpload.row_value(
                            record, biotope_record_type)
                    )
                )
            except Biotope.MultipleObjectsReturned:
                biotopes = Biotope.objects.filter(
                    biotope_type=biotope_type,
                    name=DataCSVUpload.row_value(
                        record, biotope_record_type)
                )
                if biotopes.filter(display_order__isnull=False).exists():
                    biotope = biotopes.filter(display_order__isnull=False)[0]
                else:
                    biotope = biotopes[0]
        return biotope

    def chemical_records(self, record, location_site, date):
        """Process chemical data"""
        chemical_units = {
            TEMP: TEMP,
            CONDUCTIVITY: CONDUCTIVITY,
            PH: PH,
            DISSOLVED_OXYGEN_MG: DISSOLVED_OXYGEN_MG,
            DISSOLVED_OXYGEN_PERCENT: DISSOLVED_OXYGEN_PERCENT,
            TURBIDITY: TURBIDITY,
            DEPTH_M: DEPTH_M,
            NBV: NBV,
            ORTHOPHOSPHATE: ORTHOPHOSPHATE,
            TOT: TOT,
            SILICA: SILICA,
            NH3_N: NH3_N,
            NH4_N: NH4_N,
            NO3_NO2_N: NO3_NO2_N,
            NO2_N: NO2_N,
            NO3_N: NO3_N,
            TIN: TIN,
            CHLA_B: CHLA_B,
            AFDM: AFDM
        }

        for chem_key in chemical_units:
            if chem_key not in record:
                continue
            chem_value = DataCSVUpload.row_value(record, chem_key).strip()
            if not chem_value:
                continue
            chem = Chem.objects.filter(
                chem_code__iexact=chemical_units[chem_key]
            )
            if chem.exists():
                chem = chem[0]
            else:
                chem = Chem.objects.create(
                    chem_code=chemical_units[chem_key],
                )
            chem_record, _ = ChemicalRecord.objects.get_or_create(
                date=date,
                chem=chem,
                location_site=location_site,
                survey=self.survey
            )
            chem_record.value = chem_value
            chem_record.save()

    def taxonomy(self, record):
        # if an endemism name exist in the row, check the endemism record
        # from database, if it exists, use that,
        # otherwise create a new one
        endemism = None
        if ENDEMISM in record and DataCSVUpload.row_value(record, ENDEMISM):
            endemism, endemism_created = (
                Endemism.objects.get_or_create(
                    name=DataCSVUpload.row_value(record, ENDEMISM)
                )
            )
        # -- Processing taxon species --
        species_name = DataCSVUpload.row_value(record, SPECIES_NAME)
        taxon_rank = DataCSVUpload.row_value(
            record, TAXON_RANK).upper().strip()
        # Find existing taxonomy with ACCEPTED taxonomic status
        print('module group', self.module_group, taxon_rank, species_name)
        taxa = Taxonomy.objects.filter(
            Q(canonical_name__iexact=species_name) |
            Q(legacy_canonical_name__icontains=species_name),
            rank=taxon_rank,
            taxonomic_status='ACCEPTED',
            taxongroup=self.module_group
        )
        if not taxa.exists():
            # Find existing taxonomy with any tafoxonomic status
            taxa = Taxonomy.objects.filter(
                Q(canonical_name__iexact=species_name) |
                Q(legacy_canonical_name__icontains=species_name),
                rank=taxon_rank,
                taxongroup=self.module_group
            )
        if taxa.exists():
            taxonomy = taxa[0]
        else:
            self.handle_error(
                row=record,
                message='Taxonomy does not exist for this group'
            )
            return None
        if (
                taxonomy and
                DataCSVUpload.row_value(
                    record, SPECIES_NAME) not in str(taxonomy.canonical_name)):
            taxonomy.legacy_canonical_name = DataCSVUpload.row_value(
                record, SPECIES_NAME)
        # update the taxonomy endemism if different or empty
        if not taxonomy.endemism or taxonomy.endemism != endemism:
            taxonomy.endemism = endemism
            taxonomy.save()
        return taxonomy

    def process_data(self, row):
        optional_data = {}
        # -- Location site
        location_site = self.location_site(row)
        if not location_site:
            return

        # -- UUID
        # If no uuid provided then it will be generated after collection record
        # saved
        uuid_value = ''
        if DataCSVUpload.row_value(row, UUID):
            try:
                uuid_value = uuid.UUID(
                    DataCSVUpload.row_value(row, UUID)[0:36]).hex
            except ValueError:
                self.handle_error(
                    row=row,
                    message='Bad UUID format'
                )
                return

        # -- Source reference
        message, source_reference = process_source_reference(
            reference=DataCSVUpload.row_value(row, SOURCE),
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
        else:
            optional_data['source_reference'] = source_reference

        # -- Sampling date
        sampling_date = self.parse_date(row)
        if not sampling_date:
            return

        # -- Processing Taxonomy
        taxonomy = self.taxonomy(row)
        if not taxonomy:
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
        collector = collectors
        optional_data['collector'] = DataCSVUpload.row_value(
            row, COLLECTOR_OR_OWNER)
        if len(collectors) > 0:
            collector = collectors[0]
            optional_data['collector_user'] = collectors[0]
            optional_data['owner'] = collectors[0]
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
        self.process_survey(
            row,
            location_site,
            sampling_date,
            collector=collectors[0],
        )

        # -- Optional data - Present
        if PRESENT in row:
            optional_data['present'] = bool(DataCSVUpload.row_value(
                row, PRESENT))

        # -- Optional data - Habitat
        if HABITAT in row and DataCSVUpload.row_value(row, HABITAT):
            habitat_choices = {
                v: k for k, v in
                BiologicalCollectionRecord.HABITAT_CHOICES
            }
            optional_data['collection_habitat'] = (
                habitat_choices[DataCSVUpload.row_value(row, HABITAT)]
            )

        # -- Optional data - Sampling method
        sampling_method = None
        if SAMPLING_METHOD in row and DataCSVUpload.row_value(
                row,
                SAMPLING_METHOD):
            if DataCSVUpload.row_value(
                    row,
                    SAMPLING_METHOD).lower() != 'unspecified':
                try:
                    sampling_method, sm_created = (
                        SamplingMethod.objects.get_or_create(
                            sampling_method=DataCSVUpload.row_value(
                                row,
                                SAMPLING_METHOD)
                        )
                    )
                except SamplingMethod.MultipleObjectsReturned:
                    sampling_method = (
                        SamplingMethod.objects.filter(
                            sampling_method=DataCSVUpload.row_value(
                                row,
                                SAMPLING_METHOD)
                        )
                    )[0]
        if sampling_method:
            optional_data['sampling_method'] = sampling_method

        # -- Optional data - Sampling effort
        sampling_effort = ''
        if SAMPLING_EFFORT_VALUE in row and DataCSVUpload.row_value(
                row, SAMPLING_EFFORT_VALUE):
            sampling_effort += DataCSVUpload.row_value(
                row,
                SAMPLING_EFFORT_VALUE) + ' '
        if DataCSVUpload.row_value(row, SAMPLING_EFFORT):
            sampling_effort += DataCSVUpload.row_value(row, SAMPLING_EFFORT)
        optional_data['sampling_effort'] = sampling_effort

        # -- Optional data - Processing biotope
        # Broad biotope
        optional_data['biotope'] = self.biotope(
            row,
            BROAD_BIOTOPE,
            BIOTOPE_TYPE_BROAD
        )
        # -- Optional data - Specific biotope
        optional_data['specific_biotope'] = self.biotope(
            row,
            SPECIFIC_BIOTOPE,
            BIOTOPE_TYPE_SPECIFIC
        )
        # -- Optional data - Substratum
        optional_data['substratum'] = self.biotope(
            row,
            SUBSTRATUM,
            BIOTOPE_TYPE_SUBSTRATUM
        )

        # -- Optional data - Abundance
        abundance_type = ''
        abundance_number = None

        if DataCSVUpload.row_value(row, ABUNDANCE_MEASURE):
            abundance_type = DataCSVUpload.row_value(
                row, ABUNDANCE_MEASURE).lower()
            if 'count' in abundance_type:
                abundance_type = 'number'
            elif 'density' in abundance_type:
                abundance_type = 'density'
            elif 'percentage' in abundance_type:
                abundance_type = 'percentage'
        if DataCSVUpload.row_value(row, ABUNDANCE_VALUE):
            try:
                abundance_number = float(
                    DataCSVUpload.row_value(row, ABUNDANCE_VALUE))
            except ValueError:
                pass
        if abundance_number:
            optional_data['abundance_number'] = abundance_number
        if abundance_type:
            optional_data['abundance_type'] = abundance_type

        # -- Processing chemical records
        self.chemical_records(
            row,
            location_site,
            sampling_date
        )

        record = None
        fields = {
            'site': location_site,
            'original_species_name': DataCSVUpload.row_value(
                row, SPECIES_NAME),
            'collection_date': sampling_date,
            'taxonomy': taxonomy,
            'collector_user': collector
        }
        if uuid_value:
            records = BiologicalCollectionRecord.objects.filter(
                uuid=uuid_value
            )
            if records.exists():
                records.update(**fields)
                record = records[0]
            else:
                fields['uuid'] = uuid_value

        if not record:
            try:
                record, _ = (
                    BiologicalCollectionRecord.objects.get_or_create(
                        **fields
                    )
                )
            except Exception as e:  # noqa
                self.handle_error(
                    row=row,
                    message=str(e)
                )
                return
        if not uuid_value:
            row[UUID] = record.uuid

        # Update existing data
        if self.survey:
            record.survey = self.survey
        for field in optional_data:
            setattr(
                record, field, optional_data[field])

        if self.module_group:
            record.module_group = self.module_group

        # -- Additional data
        record.additional_data = json.dumps(row)
        record.validated = True
        record.save()

        if not str(record.site.id) in self.site_ids:
            self.site_ids.append(
                str(record.site.id)
            )

        self.finish_processing_row(row, record)


class OccurrencesCSVUpload(DataCSVUpload, OccurrenceProcessor):
    model_name = 'biologicalcollectionrecord'

    def process_started(self):
        self.start_process()

    def process_ended(self):
        self.finish_process()

    def process_row(self, row):
        self.module_group = self.upload_session.module_group
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
