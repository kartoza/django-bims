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
    SearchProcess,
    source_reference_post_save_handler,
    SourceReferenceDatabase,
    SourceReferenceDocument
)
from bims.utils.user import create_users_from_string
from bims.scripts.data_upload import DataCSVUpload
from bims.tasks.location_site import update_location_context
from bims.scripts.collections_upload_source_reference import (
    process_source_reference
)
from bims.tasks.source_reference import (
    generate_source_reference_filter
)


logger = logging.getLogger('bims')


class CollectionsCSVUpload(DataCSVUpload):
    model_name = 'biologicalcollectionrecord'
    site_ids = []

    def process_started(self):
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

    def process_ended(self):
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
        SearchProcess.objects.all().delete()
        if self.site_ids:
            update_location_context(
                location_site_id=','.join(self.site_ids)
            )
        # Update source reference filter
        generate_source_reference_filter()

    def parse_date(self, row):
        # Parse date string to date object
        # Raise value error if date string is not in a valid format
        sampling_date = None
        date_string = self.row_value(row, SAMPLING_DATE)
        try:
            sampling_date = datetime.strptime(
                date_string, '%Y/%m/%d')
        except ValueError:
            sampling_date = datetime.strptime(
                date_string, '%m/%d/%Y')
        finally:
            if not sampling_date:
                self.error_file(
                    error_row=row,
                    error_message='Incorrect date format'
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
            if survey_data_key in record and self.row_value(record,
                                                            survey_data_key):
                survey_data, _ = SurveyData.objects.get_or_create(
                    name=SURVEY_DATA[survey_data_key]
                )
                survey_option = SurveyDataOption.objects.filter(
                    option__iexact=self.row_value(record,
                                                  survey_data_key).strip(),
                    survey_data=survey_data
                )
                if not survey_option.exists():
                    survey_option = SurveyDataOption.objects.create(
                        options=self.row_value(record,
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
        location_type, status = LocationType.objects.get_or_create(
            name='PointObservation',
            allowed_geometry='POINT'
        )
        site_description = self.row_value(record, SITE_DESCRIPTION)
        refined_geo = self.row_value(record, REFINED_GEO_ZONE)
        legacy_river_name = self.row_value(record, ORIGINAL_RIVER_NAME)
        longitude = self.row_value(record, LONGITUDE)
        latitude = self.row_value(record, LATITUDE)
        if not longitude or not latitude:
            self.error_file(
                error_row=record,
                error_message='Missing latitude/longitude'
            )
            return None
        record_point = Point(
            float(self.row_value(record, LONGITUDE)),
            float(self.row_value(record, LATITUDE)))
        # Create or get location site
        legacy_site_code = self.row_value(record, ORIGINAL_SITE_CODE)
        location_site_name = ''
        if self.row_value(record, LOCATION_SITE):
            location_site_name = self.row_value(record, LOCATION_SITE)
        elif self.row_value(record, WETLAND_NAME):
            location_site_name = self.row_value(record, WETLAND_NAME)
        try:
            location_site, status = (
                LocationSite.objects.get_or_create(
                    location_type=location_type,
                    geometry_point=record_point,
                    name=location_site_name,
                    legacy_site_code=legacy_site_code
                )
            )
        except LocationSite.MultipleObjectsReturned:
            location_site = LocationSite.objects.filter(
                location_type=location_type,
                geometry_point=record_point,
                name=location_site_name,
                legacy_site_code=legacy_site_code
            )[0]
        if site_description:
            location_site.site_description = site_description
        if refined_geo:
            location_site.refined_geomorphological = refined_geo
        if legacy_river_name:
            location_site.legacy_river_name = legacy_river_name
        if not location_site.site_code:
            site_code = location_site.generate_site_code()
            location_site.site_code = site_code
        location_site.save()
        return location_site

    def biotope(self, record, biotope_record_type, biotope_type):
        """Process biotope data"""
        biotope = None
        if (
                self.row_value(record, biotope_record_type) and
                self.row_value(
                    record, biotope_record_type).lower() != 'unspecified'):
            try:
                biotope, biotope_created = (
                    Biotope.objects.get_or_create(
                        biotope_type=biotope_type,
                        name=self.row_value(record, biotope_record_type)
                    )
                )
            except Biotope.MultipleObjectsReturned:
                biotopes = Biotope.objects.filter(
                    biotope_type=biotope_type,
                    name=self.row_value(record, biotope_record_type)
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
            chem_value = self.row_value(record, chem_key).strip()
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
        if ENDEMISM in record and self.row_value(record, ENDEMISM):
            endemism, endemism_created = (
                Endemism.objects.get_or_create(
                    name=self.row_value(record, ENDEMISM)
                )
            )
        # -- Processing taxon species --
        species_name = self.row_value(record, SPECIES_NAME)
        taxon_rank = self.row_value(record, TAXON_RANK).upper().strip()
        # Find existing taxonomy with ACCEPTED taxonomic status
        taxa = Taxonomy.objects.filter(
            Q(canonical_name__iexact=species_name) |
            Q(legacy_canonical_name__icontains=species_name),
            rank=taxon_rank,
            taxonomic_status='ACCEPTED',
            taxongroup=self.upload_session.module_group
        )
        if not taxa.exists():
            # Find existing taxonomy with any taxonomic status
            taxa = Taxonomy.objects.filter(
                Q(canonical_name__iexact=species_name) |
                Q(legacy_canonical_name__icontains=species_name),
                rank=taxon_rank,
                taxongroup=self.upload_session.module_group
            )
        if taxa.exists():
            taxonomy = taxa[0]
        else:
            self.error_file(
                error_row=record,
                error_message='Taxonomy does not exist for this group'
            )
            return None
        if (
                taxonomy and
                self.row_value(
                    record, SPECIES_NAME) not in str(taxonomy.canonical_name)):
            taxonomy.legacy_canonical_name = self.row_value(
                record, SPECIES_NAME)
        # update the taxonomy endemism if different or empty
        if not taxonomy.endemism or taxonomy.endemism != endemism:
            taxonomy.endemism = endemism
            taxonomy.save()
        return taxonomy

    def process_row(self, row):
        optional_data = {}
        # -- Location site
        location_site = self.location_site(row)
        if not location_site:
            return

        # -- UUID
        # If no uuid provided then it will be generated after collection record
        # saved
        uuid_value = ''
        if self.row_value(row, UUID):
            try:
                uuid_value = uuid.UUID(self.row_value(row, UUID)[0:36]).hex
            except ValueError:
                self.error_file(
                    error_row=row,
                    error_message='Bad UUID format'
                )
                return

        # -- Source reference
        message, source_reference = process_source_reference(
            reference=self.row_value(row, SOURCE),
            reference_category = self.row_value(row, REFERENCE_CATEGORY),
            doi = self.row_value(row, DOI),
            document_title = self.row_value(row, DOCUMENT_TITLE),
            document_link = self.row_value(row, DOCUMENT_UPLOAD_LINK),
            document_url = self.row_value(row, DOCUMENT_URL),
            document_author = self.row_value(row, DOCUMENT_AUTHOR),
            source_year = self.row_value(row, SOURCE_YEAR)
        )
        if message and not source_reference:
            # Source reference data from csv exists but not created
            self.error_file(
                error_row=row,
                error_message=message
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
        custodian = self.row_value(row, CUSTODIAN)
        collectors = create_users_from_string(
            self.row_value(row, COLLECTOR_OR_OWNER))
        if not collectors:
            self.error_file(
                error_row=row,
                error_message='Missing collector/owner'
            )
            return
        collector = collectors
        optional_data['collector'] = self.row_value(row, COLLECTOR_OR_OWNER)
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
                    _collector.organization = self.row_value(row, CUSTODIAN)
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
            optional_data['present'] = bool(self.row_value(row, PRESENT))

        # -- Process origin
        category = None
        if CATEGORY in row:
            category = self.row_value(row, CATEGORY).lower()
        if ORIGIN in row and self.row_value(row, ORIGIN):
            origin = self.row_value(row, ORIGIN)
            if (
                    'translocated' in origin.lower() or
                    'non-native' in origin.lower()):
                category = 'alien'
            elif 'native' == origin.lower():
                category = 'native'
            else:
                category = None
        if not category:
            category = taxonomy.origin
        optional_data['category'] = category

        # -- Optional data - Habitat
        if HABITAT in row and self.row_value(row, HABITAT):
            habitat_choices = {
                v: k for k, v in
                BiologicalCollectionRecord.HABITAT_CHOICES
            }
            optional_data['collection_habitat'] = (
                habitat_choices[self.row_value(row, HABITAT)]
            )

        # -- Optional data - Sampling method
        sampling_method = None
        if SAMPLING_METHOD in row and self.row_value(
                row,
                SAMPLING_METHOD):
            if self.row_value(
                    row,
                    SAMPLING_METHOD).lower() != 'unspecified':
                try:
                    sampling_method, sm_created = (
                        SamplingMethod.objects.get_or_create(
                            sampling_method=self.row_value(row,
                                                           SAMPLING_METHOD)
                        )
                    )
                except SamplingMethod.MultipleObjectsReturned:
                    sampling_method = (
                        SamplingMethod.objects.filter(
                            sampling_method=self.row_value(row,
                                                           SAMPLING_METHOD)
                        )
                    )[0]
        if sampling_method:
            optional_data['sampling_method'] = sampling_method

        # -- Optional data - Sampling effort
        sampling_effort = ''
        if SAMPLING_EFFORT_VALUE in row and self.row_value(
                row, SAMPLING_EFFORT_VALUE):
            sampling_effort += self.row_value(
                row,
                SAMPLING_EFFORT_VALUE) + ' '
        if self.row_value(row, SAMPLING_EFFORT):
            sampling_effort += self.row_value(row, SAMPLING_EFFORT)
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

        if self.row_value(row, ABUNDANCE_MEASURE):
            abundance_type = self.row_value(row, ABUNDANCE_MEASURE).lower()
            if 'count' in abundance_type:
                abundance_type = 'number'
            elif 'density' in abundance_type:
                abundance_type = 'density'
            elif 'percentage' in abundance_type:
                abundance_type = 'percentage'
        if self.row_value(row, ABUNDANCE_VALUE):
            try:
                abundance_number = float(
                    self.row_value(row, ABUNDANCE_VALUE))
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
            'original_species_name': self.row_value(row, SPECIES_NAME),
            'collection_date': sampling_date,
            'taxonomy': taxonomy,
            'category': category,
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
                self.error_file(
                    error_row=row,
                    error_message=str(e)
                )
                return
        if not uuid_value:
            row[UUID] = record.uuid

        # Update existing data
        if self.survey:
            record.survey = self.survey
        if self.upload_session.module_group:
            record.module_group = self.upload_session.module_group
        for field in optional_data:
            setattr(
                record, field, optional_data[field])

        # -- Additional data
        record.additional_data = json.dumps(row)
        record.validated = True
        record.save()

        if not str(record.site.id) in self.site_ids:
            self.site_ids.append(
                str(record.site.id)
            )

        self.success_file(
            success_row=row,
            data_id=record.id
        )
