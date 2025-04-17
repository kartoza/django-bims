import csv
import uuid
import json
import logging

from preferences import preferences

from bims.scripts.collection_csv_keys import *  # noqa
from datetime import datetime

from django.contrib.gis.geos import Point
from django.db.models import Q

from bims.models import (
    LocationType,
    LocationSite,
    Endemism,
    BiologicalCollectionRecord,
    SamplingMethod,
    Taxonomy,
    ChemicalRecord,
    Chem,
    Biotope,
    BIOTOPE_TYPE_BROAD,
    BIOTOPE_TYPE_SPECIFIC,
    BIOTOPE_TYPE_SUBSTRATUM,
    Survey,
    SurveyData,
    SurveyDataOption,
    SurveyDataValue,
    Hydroperiod,
    WetlandIndicatorStatus,
    RecordType,
    AbundanceType,
    SamplingEffortMeasure,
)
from bims.signals.utils import disconnect_bims_signals, connect_bims_signals
from bims.utils.feature_info import get_feature_centroid
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
    park_centroid = {}
    parks_data = {}
    section_data = {}

    def start_process(self):
        disconnect_bims_signals()

    def update_location_site_context(self):
        update_location_context.delay(
            location_site_id=','.join(self.site_ids),
            generate_site_code=True
        )

    def finish_process(self):
        if self.site_ids and self.fetch_location_context:
            self.update_location_site_context()

        generate_spatial_scale_filter()
        # Update source reference filter
        generate_source_reference_filter()

        connect_bims_signals()

    def handle_error(self, row, message):
        pass

    def finish_processing_row(self, row, record):
        pass

    def parse_date(self, row):
        def try_parse_date(date_str, date_format):
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                return None

        # Retrieve the date string from the row
        date_string = DataCSVUpload.row_value(row, SAMPLING_DATE)
        if not date_string:
            date_string = DataCSVUpload.row_value(row, SAMPLING_DATE_2)

        # If date_string is still None, handle the error
        if not date_string:
            self.handle_error(row=row, message='Date string is missing')
            return None

        # Define possible date formats
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d/%m/%Y',
        ]

        # Attempt to parse the date string using the defined formats
        for date_format in date_formats:
            sampling_date = try_parse_date(date_string, date_format)
            if sampling_date:
                return sampling_date

        # If no valid format found, handle the error
        self.handle_error(row=row, message='Incorrect date format')
        return None

    def process_survey(self, record, location_site, sampling_date, collector):
        """Process survey data"""
        try:
            self.survey, _ = Survey.objects.get_or_create(
                site=location_site,
                date=sampling_date,
                collector_user=collector,
                owner=collector,
                validated=True
            )
            if not self.survey.uuid:
                self.survey.save()

        except Survey.MultipleObjectsReturned:
            self.survey = Survey.objects.filter(
                site=location_site,
                date=sampling_date,
                collector_user=collector,
                owner=collector,
                validated=True
            ).first()

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

        # -- Ecosystem type
        ecosystem_type = DataCSVUpload.row_value(
            record, ECOSYSTEM_TYPE)
        if not ecosystem_type:
            ecosystem_type = DataCSVUpload.row_value(
                record, ECOSYSTEM_TYPE_2)

        location_type, status = LocationType.objects.get_or_create(
            name='PointObservation',
            allowed_geometry='POINT'
        )
        site_description = DataCSVUpload.row_value(record, SITE_DESCRIPTION)
        refined_geo = DataCSVUpload.row_value(record, REFINED_GEO_ZONE)
        if not refined_geo:
            refined_geo = DataCSVUpload.row_value(record, ORIGINAL_GEO_ZONE)
        wetland_name = DataCSVUpload.row_value(record, WETLAND_NAME)
        user_wetland_name = DataCSVUpload.row_value(record, USER_WETLAND_NAME)
        user_hydrogeomorphic_type = DataCSVUpload.row_value(
            record,
            USER_HYDROGEOMORPHIC_TYPE
        )
        legacy_river_name = DataCSVUpload.row_value(
            record, USER_RIVER_NAME
        )
        if not legacy_river_name:
            legacy_river_name = DataCSVUpload.row_value(
                record, ORIGINAL_RIVER_NAME)

        user_river_or_wetland_name = DataCSVUpload.row_value(
            record, USER_RIVER_OR_WETLAND_NAME
        )

        if user_river_or_wetland_name:
            if ecosystem_type.lower() == 'wetland':
                user_wetland_name = user_river_or_wetland_name
            else:
                legacy_river_name = user_river_or_wetland_name

        longitude = DataCSVUpload.row_value(record, LONGITUDE)
        latitude = DataCSVUpload.row_value(record, LATITUDE)

        park_name = DataCSVUpload.row_value(record, PARK_OR_MPA_NAME)
        section_name = DataCSVUpload.row_value(record, SECTION_NAME)

        accuracy_of_coordinates = DataCSVUpload.row_value(
            record, ACCURACY_OF_COORDINATES
        )
        if not accuracy_of_coordinates:
            accuracy_of_coordinates = 100

        if not longitude and not latitude and section_name:
            section_file = preferences.SiteSetting.section_layer_csv
            if section_file:
                if not self.section_data:
                    with open(section_file.path, mode='r') as file:
                        reader = csv.DictReader(file, delimiter=',')
                        section_key = reader.fieldnames[0].strip().lower()
                        for row in reader:
                            _section_name = row[section_key].strip().lower()
                            lat = float(row['x'])
                            lon = float(row['y'])
                            self.section_data[_section_name] = {
                                'lat': lat,
                                'lon': lon
                            }
                section_name_low = section_name.strip().lower()
                if section_name_low in self.section_data:
                    latitude = self.section_data[section_name_low]['lat']
                    longitude = self.section_data[section_name_low]['lon']

        if not longitude and not latitude and park_name:
            park_mpa_csv_file = preferences.SiteSetting.park_layer_csv
            wfs_url = preferences.SiteSetting.park_wfs_url
            layer_name = preferences.SiteSetting.park_wfs_layer_name
            attribute_key = preferences.SiteSetting.park_wfs_attribute_key
            attribute_value = park_name

            if park_mpa_csv_file:
                if not self.parks_data:
                    with open(park_mpa_csv_file.path, mode='r') as file:
                        reader = csv.DictReader(file, delimiter=',')
                        for row in reader:
                            _park_name = (
                                row['Park_Name'].strip().lower()
                            )
                            lat = float(row['x'])
                            lon = float(row['y'])
                            self.parks_data[_park_name] = {
                                'lat': lat,
                                'lon': lon
                            }
                park_name_low = park_name.strip().lower()
                if park_name_low in self.parks_data:
                    latitude = self.parks_data[
                        park_name_low
                    ]['lat']
                    longitude = self.parks_data[
                        park_name_low
                    ]['lon']
                else:
                    self.handle_error(
                        row=record,
                        message='Park or MPA name does not exist in the database'
                    )
                    return None
            else:
                if park_name in self.park_centroid:
                    latitude = self.park_centroid[park_name][0]
                    longitude = self.park_centroid[park_name][1]
                else:
                    # Check if there is already site with the same park name
                    site = LocationSite.objects.filter(
                        name=park_name
                    ).first()
                    if site:
                        latitude = site.latitude
                        longitude = site.longitude
                        self.park_centroid[site.name] = [latitude, longitude]
                        # Check if site with same park name and accuracy of coordinates exists
                        site = LocationSite.objects.filter(
                            name=park_name,
                            accuracy_of_coordinates=accuracy_of_coordinates
                        ).exclude(site_code='').first()
                        if site:
                            # Return existing site
                            return site
                    else:
                        park_centroid = get_feature_centroid(
                            wfs_url,
                            layer_name,
                            attribute_key=attribute_key,
                            attribute_value=attribute_value
                        )
                        if park_centroid:
                            latitude = park_centroid[0]
                            longitude = park_centroid[1]
                            self.park_centroid[park_name] = park_centroid
                        else:
                            self.handle_error(
                                row=record,
                                message='Park or MPA name does not exist in the database'
                            )
                            return None

        if not longitude or not latitude:
            self.handle_error(
                row=record,
                message='Missing latitude/longitude'
            )
            return None

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            self.handle_error(
                row=record,
                message='Incorrect latitude or longitude format'
            )
            return None

        record_point = Point(
            longitude,
            latitude)
        # Create or get location site
        legacy_site_code = DataCSVUpload.row_value(record, USER_SITE_CODE)
        if not legacy_site_code:
            legacy_site_code = DataCSVUpload.row_value(
                record, ORIGINAL_SITE_CODE)
        location_site_name = ''
        if DataCSVUpload.row_value(record, LOCATION_SITE):
            location_site_name = DataCSVUpload.row_value(record, LOCATION_SITE)
        elif wetland_name:
            location_site_name = wetland_name
        elif park_name:
            location_site_name = park_name
        elif section_name:
            location_site_name = section_name

        # Find existing location site by data source site code
        data_source = preferences.SiteSetting.default_data_source.upper()
        existing_site_code = DataCSVUpload.row_value(
            record, '{} Site Code'.format(
                data_source
            ))
        if not existing_site_code:
            existing_site_code = DataCSVUpload.row_value(
                record, 'Site Code')
        if existing_site_code:
            location_site = LocationSite.objects.filter(
                site_code__iexact=existing_site_code.strip()
            ).first()

        # Find existing location site by lat and lon
        if not location_site:
            if len(str(latitude)) > 5 and len(str(longitude)) > 5:
                location_site = LocationSite.objects.filter(
                    latitude__startswith=latitude,
                    longitude__startswith=longitude,
                    ecosystem_type=ecosystem_type
                ).first()

        if not location_site:
            location_site = LocationSite.objects.filter(
                geometry_point=record_point,
                ecosystem_type=ecosystem_type
            ).first()
            if not location_site:
                location_site, status = (
                    LocationSite.objects.get_or_create(
                        geometry_point=record_point,
                        ecosystem_type=ecosystem_type,
                        location_type=location_type
                    )
                )

        if not location_site.name and location_site_name:
            location_site.name = location_site_name
        if not location_site.location_type:
            location_site.location_type = location_type
        if not location_site.legacy_site_code and legacy_site_code:
            location_site.legacy_site_code = legacy_site_code
        if not location_site.site_description and site_description:
            location_site.site_description = site_description
        if refined_geo:
            location_site.refined_geomorphological = refined_geo
        if legacy_river_name:
            location_site.legacy_river_name = legacy_river_name
        if wetland_name or location_site.wetland_name:
            location_site.wetland_name = wetland_name
        if user_wetland_name or location_site.user_wetland_name:
            location_site.user_wetland_name = user_wetland_name
        if user_hydrogeomorphic_type or location_site.user_hydrogeomorphic_type:
            location_site.user_hydrogeomorphic_type = user_hydrogeomorphic_type
        if not location_site.site_code:
            site_code, catchments_data = generate_site_code(
                location_site,
                lat=location_site.latitude,
                lon=location_site.longitude,
                ecosystem_type=location_site.ecosystem_type,
                wetland_name=user_wetland_name,
                **{
                    'site_desc': site_description,
                    'site_name': location_site_name
                }
            )
            location_site.site_code = site_code
        if accuracy_of_coordinates:
            location_site.accuracy_of_coordinates = accuracy_of_coordinates
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
            record, TAXON_RANK
        ).replace(' ', '').upper().strip()
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

        # -- UUID
        # If no uuid provided then it will be generated after collection record
        # saved
        uuid_value = ''
        if DataCSVUpload.row_value(row, UUID):
            try:
                uuid.UUID(DataCSVUpload.row_value(row, UUID)[0:36])
                uuid_value = DataCSVUpload.row_value(row, UUID)
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

        # -- Location site
        location_site = self.location_site(row)
        if not location_site:
            return

        # -- Processing collectors
        custodian = DataCSVUpload.row_value(row, CUSTODIAN)
        collectors = create_users_from_string(
            DataCSVUpload.row_value(row, COLLECTOR_OR_OWNER))
        if not collectors:
            collectors = create_users_from_string(
                DataCSVUpload.row_value(row, COLLECTOR_OR_OWNER_2))
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
        habitat_value = DataCSVUpload.row_value(row, HABITAT)
        if HABITAT in row and habitat_value:
            habitat_choices = {
                v: k for k, v in
                BiologicalCollectionRecord.HABITAT_CHOICES
            }
            if habitat_value in habitat_choices:
                habitat_value = habitat_choices[habitat_value]
            optional_data['collection_habitat'] = (
                habitat_value
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
                SAMPLING_EFFORT_VALUE)
        optional_data['sampling_effort'] = sampling_effort

        sampling_effort_measure = DataCSVUpload.row_value(row, SAMPLING_EFFORT)
        if 'min' in sampling_effort_measure.lower():
            sampling_effort_measure, _ = SamplingEffortMeasure.objects.get_or_create(
                name='Time(min)'
            )
        elif (
                'area' in sampling_effort_measure.lower() or
                'm2' in sampling_effort_measure.lower() or
                'meter' in sampling_effort_measure.lower() or
                'metre' in sampling_effort_measure.lower()
        ):
            sampling_effort_measure, _ = SamplingEffortMeasure.objects.get_or_create(
                name='Area(m2)'
            )
        elif 'replicates' in sampling_effort_measure.lower():
            sampling_effort_measure, _ = SamplingEffortMeasure.objects.get_or_create(
                name='Replicates'
            )
        else:
            sampling_effort_measure, _ = SamplingEffortMeasure.objects.get_or_create(
                name=sampling_effort_measure
            )

        if sampling_effort_measure:
            optional_data['sampling_effort_link'] = sampling_effort_measure

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
        abundance_type = None
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

            abundance_type = AbundanceType.objects.filter(
                name__icontains=abundance_type
            ).first()

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

        # -- Record type
        record_type_str = DataCSVUpload.row_value(row, RECORD_TYPE)
        if record_type_str:
            record_type = RecordType.objects.filter(
                name__iexact=record_type_str
            ).first()
            if not record_type:
                record_type = RecordType.objects.create(
                    name=record_type_str
                )
        else:
            record_type = None
        optional_data['record_type'] = record_type

        # -- Wetland component
        hydroperiod = DataCSVUpload.row_value(row, HYDROPERIOD)
        wetland_indicator_status = (
            DataCSVUpload.row_value(
                row,
                WETLAND_INDICATOR_STATUS
            )
        )
        if hydroperiod:
            hydroperiod = Hydroperiod.objects.filter(
                name__iexact=hydroperiod
            ).first()
        else:
            hydroperiod = None

        optional_data['hydroperiod'] = hydroperiod

        if wetland_indicator_status:
            wetland_indicator_status = WetlandIndicatorStatus.objects.filter(
                name__iexact=wetland_indicator_status
            ).first()
        else:
            wetland_indicator_status = None

        optional_data['wetland_indicator_status'] = wetland_indicator_status

        # -- Processing chemical records
        self.chemical_records(
            row,
            location_site,
            sampling_date
        )

        species_name = DataCSVUpload.row_value(
            row, VERBATUM_NAME
        )

        if not species_name:
            species_name = DataCSVUpload.row_value(
                row, SPECIES_NAME
            )

        certainty_of_identification = DataCSVUpload.row_value(
            row, CERTAINTY_OF_IDENTIFICATION
        )

        date_accuracy = DataCSVUpload.row_value(
            row, DATE_ACCURACY
        )

        data_type = DataCSVUpload.row_value(
            row, DATA_TYPE
        )
        if data_type:
            data_type = data_type.lower()
            if 'public' in data_type:
                data_type = 'public'
            elif 'private' in data_type:
                data_type = 'private'
            elif 'sensitive' in data_type:
                data_type = 'sensitive'
            else:
                data_type = ''

        identified_by = DataCSVUpload.row_value(
            row, IDENTIFIED_BY
        )

        record = None
        fields = {
            'site': location_site,
            'original_species_name': species_name,
            'collection_date': sampling_date,
            'taxonomy': taxonomy,
            'collector_user': collector,
            'validated': True,
            'certainty_of_identification': (
                certainty_of_identification if certainty_of_identification else ''
            ),
            'date_accuracy': date_accuracy.lower() if date_accuracy else '',
            'data_type': data_type,
            'identified_by': identified_by if identified_by else ''
        }
        if uuid_value:
            uuid_without_hyphen = uuid_value.replace('-', '')
            records = BiologicalCollectionRecord.objects.filter(
                Q(uuid=uuid_value) |
                Q(uuid=uuid_without_hyphen)
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

        # -- Ecosystem type
        ecosystem_type = DataCSVUpload.row_value(
            row, ECOSYSTEM_TYPE)
        if not ecosystem_type:
            ecosystem_type = DataCSVUpload.row_value(
                row, ECOSYSTEM_TYPE_2
            )
        record.ecosystem_type = ecosystem_type

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
