# -*- coding: utf-8 -*-
import requests
import ast
import re
import os
import csv
import json
import uuid
from datetime import datetime, date

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q, signals

from bims.utils.logger import log
from bims.models import (
    LocationType,
    LocationSite,
    Endemism,
    BiologicalCollectionRecord,
    SamplingMethod,
    VernacularName,
    Taxonomy,
    SourceReference,
    DatabaseRecord,
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
    TaxonGroup
)
from td_biblio.models.bibliography import Entry, Author, AuthorEntryRank
from td_biblio.utils.loaders import DOILoader, DOILoaderError
from bims.utils.fetch_gbif import (
    fetch_all_species_from_gbif, check_taxa_duplicates
)
from bims.utils.user import create_users_from_string
from geonode.documents.models import Document
from bims.models.taxonomy import taxonomy_pre_save_handler

SPECIES_NAME = 'Taxon'
TAXON_RANK = 'Taxon rank'
LATITUDE = 'Latitude'
LONGITUDE = 'Longitude'
LOCATION_SITE = 'Original River Name'
ORIGINAL_SITE_CODE = 'Original Site Code'
ORIGINAL_RIVER_NAME = 'Original River Name'
FBIS_SITE_CODE = 'FBIS Site Code'
SITE_DESCRIPTION = 'Site description'
REFINED_GEO_ZONE = 'Refined Geomorphological Zone'
ENDEMISM = 'Endemism'
CATEGORY = 'Category'
ORIGIN = 'Origin'
HABITAT = 'Habitat'
SAMPLING_METHOD = 'Sampling method'
SAMPLING_EFFORT = 'Sampling effort measure'
SAMPLING_EFFORT_VALUE = 'Sampling effort value'
ABUNDANCE_MEASURE = 'Abundance measure'
ABUNDANCE_VALUE = 'Abundance value'
CATCH_NUMBER = 'Catch/number'
CATCH_PER_UNIT = 'Catch Per Unit Effort (CPUE)'
# HYDRAULIC_BIOTOPE = 'Hydraulic biotope'
BROAD_BIOTOPE = 'Broad biotope'
SPECIFIC_BIOTOPE = 'Specific biotope'
SUBSTRATUM = 'Substratum'

# Chemical records
TEMP = 'TEMP'
CONDUCTIVITY = 'COND'
PH = 'PH'
DISSOLVED_OXYGEN_PERCENT = 'DOPER'
DISSOLVED_OXYGEN_MG = 'DO'
TURBIDITY = 'TURB'
ORTHOPHOSPHATE = 'SRP'
TOT = 'TOT-P'
SILICA = 'SI'
NH4_N = 'NH4-N'
NH3_N = 'NH3-N'
NO3_NO2_N = 'NO3+NO2-N'
NO2_N = 'NO2-N'
NO3_N = 'NO3-N'
TIN = 'TIN'
AFDM = 'AFDM'
CHLA_B = 'CHLA-B'

DEPTH_M = 'Depth'
NBV = 'Near Bed Velocity'
COLLECTOR_OR_OWNER = 'Collector/Owner'
CUSTODIAN = 'Collector/Owner Institute'
NUMBER_OF_REPLICATES = 'Number of replicates'
SAMPLING_DATE = 'Sampling Date'
UUID = 'UUID'
COLLECTOR = 'Collector/Owner'
NOTES = 'Notes'
REFERENCE = 'Reference'
REFERENCE_CATEGORY = 'Reference category'
DOI = 'DOI'
DOCUMENT_UPLOAD_LINK = 'Document Upload Link'
DOCUMENT_URL = 'URL'
DOCUMENT_TITLE = 'Title'
DOCUMENT_AUTHOR = 'Author(s)'
SOURCE_YEAR = 'Year'
SOURCE = 'Source'
PRESENT = 'Present'
COMMON_NAME = 'Common Name'

# Abiotic categorical values
WATER_LEVEL = 'Water Level'
WATER_TURBIDITY = 'Water Turbidity'
EMBEDDEDNESS = 'Embeddedness'


class Command(BaseCommand):
    """Import fish data from file"""
    file_name = 'CFR.Fish.csv'
    group_key = ''
    group = None

    summary = {}
    data_added = 0
    data_updated = 0
    data_failed = 0
    data_duplicated = 0
    errors = []
    warnings = []
    survey = None

    def add_arguments(self, parser):
        parser.add_argument(
            '-file',
            '--csv-file',
            dest='csv_file',
            default=self.file_name,
            help='CSV file for updating sites data'
        )
        parser.add_argument(
            '-source',
            '--source-collection',
            dest='source_collection',
            default='CFE Fish Data',
            help='Source collection name for this file'
        )
        parser.add_argument(
            '-ad',
            '--additional-data',
            dest='additional_data',
            default='{}',
            help='Additional data in json format'
        )
        parser.add_argument(
            '-oa',
            '--only-add',
            dest='only_add',
            default=False,
            help='Only process new data'
        )
        parser.add_argument(
            '-so',
            '--sites-only',
            dest='sites_only',
            default='False',
            help='Only ingest sites'
        )
        parser.add_argument(
            '-g',
            '--group',
            dest='group_key',
            default='',
            help='Module group name'
        )
        parser.add_argument(
            '-ft',
            '--find-taxon',
            dest='find_taxon',
            default='True',
            help='Should also find the taxon from gbif'
        )

    def add_to_error_summary(self, error_message, row, add_to_error=True, only_log=False):
        error_message = '{id} : {error}'.format(
            id=row+2,
            error=error_message
        )
        log(error_message)
        if only_log:
            return
        if add_to_error:
            self.errors.append(error_message)
            self.data_failed += 1
        else:
            self.warnings.append(error_message)

    def row_value(self, row, key):
        value = ''
        if key in row and row[key]:
            value = row[key]
            value = value.replace('\xa0', ' ')
            value = value.replace('\xc2', '')
            value = value.replace('\\xa0', '')
            value = value.strip()
            value = re.sub(' +', ' ', value)
            try:
                value.decode('utf-8')
            except ValueError:
                value = value.decode('windows-1252')
        return value

    def import_additional_data(self, collection_record, record):
        """
        Override this to import additional data to collection_record.
        :param collection_record: BiologicalCollectionRecord object
        :param record: csv record
        """
        pass

    def parse_date(self, date_string):
        # Parse date string to date object
        # Raise value error if date string is not in a valid format
        sampling_date = None
        try:
            sampling_date = datetime.strptime(
                date_string, '%Y/%m/%d')
        except ValueError:
            sampling_date = datetime.strptime(
                date_string, '%m/%d/%Y')
        finally:
            if not sampling_date:
                raise ValueError('Incorrect Date format')
            return sampling_date

    def disconnect_signals(self):
        signals.post_save.disconnect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
        signals.post_save.disconnect(
            location_site_post_save_handler,
            sender=LocationSite
        )
        signals.pre_save.disconnect(
            taxonomy_pre_save_handler,
            sender=Taxonomy
        )

    def reconnect_signals(self):
        signals.post_save.connect(
            collection_post_save_handler
        )
        signals.post_save.connect(
            location_site_post_save_handler
        )

    def source_reference(self, record, index):
        source_reference = None
        reference = self.row_value(record, SOURCE)
        reference_category = self.row_value(record, REFERENCE_CATEGORY)
        doi = self.row_value(record, DOI)
        document_link = self.row_value(record, DOCUMENT_UPLOAD_LINK)
        document_url = self.row_value(record, DOCUMENT_URL)
        document_id = 0
        document = None
        source_reference_found = False

        # if there is document link, get the id of the document
        if document_link:
            try:
                doc_split = document_link.split('/')
                document_id = int(doc_split[len(doc_split) - 1])
                document = Document.objects.get(id=document_id)
            except (ValueError, Document.DoesNotExist):
                log('Document {} does not exist'.format(document_id))

        # if there is document url, get or create document based on url
        if document_url:
            document_fields = {
                'doc_url': document_url,
                'title': self.row_value(record, DOCUMENT_TITLE),
            }
            if self.row_value(record, SOURCE_YEAR):
                document_fields['date'] = date(
                    year=int(self.row_value(record, SOURCE_YEAR)),
                    month=1,
                    day=1
                )
            authors = create_users_from_string(self.row_value(record, DOCUMENT_AUTHOR))
            if len(authors) > 0:
                author = authors[0]
            else:
                author = None
            document_fields['owner'] = author
            document, document_created = Document.objects.get_or_create(
                **document_fields
            )

        # if DOI provided, check in bibliography records
        if doi:
            try:
                try:
                    entry = Entry.objects.get(
                        doi=doi
                    )
                except Entry.MultipleObjectsReturned:
                    entry = Entry.objects.filter(doi=doi)[0]
                try:
                    source_reference = SourceReferenceBibliography.objects.get(
                        source=entry
                    )
                except SourceReferenceBibliography.DoesNotExist:
                    source_reference = (
                        SourceReferenceBibliography.objects.create(
                            source=entry
                        )
                    )
                source_reference_found = True
            except Entry.DoesNotExist:
                doi_loader = DOILoader()
                try:
                    doi_loader.load_records(DOIs=[doi])
                    doi_loader.save_records()
                    entry = Entry.objects.get(doi__iexact=doi)
                    source_reference = (
                        SourceReference.create_source_reference(
                            category='bibliography',
                            source_id=entry.id,
                            note=None
                        )
                    )
                    source_reference_found = True
                except (DOILoaderError, requests.exceptions.HTTPError, Entry.DoesNotExist):
                    self.add_to_error_summary(
                        'Error Fetching DOI : {doi}'.format(
                            doi=doi,
                        ),
                        index,
                        only_log=True
                    )
                except Entry.MultipleObjectsReturned:
                    entry = Entry.objects.filter(doi__iexact=doi)[0]
                    source_reference = (
                        SourceReference.create_source_reference(
                            category='bibliography',
                            source_id=entry.id,
                            note=None
                        )
                    )
                    source_reference_found = True

        if not source_reference_found:
            if (
                    'peer-reviewed' in reference_category.lower()
            ):
                # Peer reviewed
                # should be bibliography type
                # If url, title, year, and author(s) exists, crete new entry
                if (
                        self.row_value(record, DOCUMENT_URL) and
                        self.row_value(record, DOCUMENT_TITLE) and
                        self.row_value(record, DOCUMENT_AUTHOR) and
                        self.row_value(record, SOURCE_YEAR)
                ):
                    optional_values = {}
                    if doi:
                        optional_values['doi'] = doi
                    entry, _ = Entry.objects.get_or_create(
                        url=self.row_value(record, DOCUMENT_URL),
                        title=self.row_value(record, DOCUMENT_TITLE),
                        publication_date=date(int(self.row_value(record, SOURCE_YEAR)), 1, 1),
                        is_partial_publication_date=True,
                        type='article',
                        **optional_values
                    )
                    authors = create_users_from_string(self.row_value(record, DOCUMENT_AUTHOR))
                    rank = 1
                    for author in authors:
                        _author, _ = Author.objects.get_or_create(
                            first_name=author.first_name,
                            last_name=author.last_name,
                            user=author
                        )
                        AuthorEntryRank.objects.get_or_create(
                            author=_author,
                            entry=entry,
                            rank=rank
                        )
                        rank += 1
                    try:
                        source_reference = SourceReferenceBibliography.objects.get(
                            source=entry
                        )
                    except SourceReferenceBibliography.DoesNotExist:
                        source_reference = (
                            SourceReferenceBibliography.objects.create(
                                source=entry
                            )
                        )
                else:
                    raise ValueError('Peer reviewed should have a DOI')
            elif (
                    reference_category.lower().startswith('published') or
                    'thesis' in reference_category.lower()
            ):
                # Document
                if document:
                    source_reference = (
                        SourceReference.create_source_reference(
                            category='document',
                            source_id=document.id,
                            note=None
                        )
                    )
            elif 'database' in reference_category.lower():
                reference_name = reference
                if self.row_value(record, SOURCE_YEAR):
                    reference_name += ', ' + self.row_value(record, SOURCE_YEAR)
                database_record, dr_created = (
                    DatabaseRecord.objects.get_or_create(
                        name=reference_name
                    )
                )
                source_reference = (
                    SourceReference.create_source_reference(
                        category='database',
                        source_id=database_record.id,
                        note=None
                    )
                )
            else:
                # Unpublished data
                reference_name = reference
                if self.row_value(record, SOURCE_YEAR):
                    reference_name += ', ' + self.row_value(record, SOURCE_YEAR)
                source_reference = (
                    SourceReference.create_source_reference(
                        category=None,
                        source_id=None,
                        note=reference_name
                    )
                )
        if (
                document and
                source_reference and
                not isinstance(source_reference.source, Document)):
            source_reference.document = document
            source_reference.save()

        if reference and source_reference:
            source_reference.source_name = reference
        elif reference and not source_reference:
            self.add_to_error_summary(
                'Reference {} is not created'.format(
                    reference
                ),
                index)

        return source_reference

    def taxonomy(self, record, index):
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
        # Find existing taxonomy
        taxa = Taxonomy.objects.filter(
            Q(canonical_name__iexact=species_name) |
            Q(legacy_canonical_name__icontains=species_name),
            rank=taxon_rank,
            taxonomic_status='ACCEPTED'
        )
        if not taxa.exists():
            taxa = Taxonomy.objects.filter(
                Q(canonical_name__iexact=species_name) |
                Q(legacy_canonical_name__icontains=species_name),
                rank=taxon_rank
            )
        if taxa.exists():
            try:
                taxonomy = taxa[0]
            except Exception as e: #  noqa
                taxonomy = taxa[0]
                print(str(e))
        else:
            if self.find_taxon:
                # if not exist, search from gbif
                # Fetch from gbif
                taxonomy = fetch_all_species_from_gbif(
                    species=species_name,
                    taxonomic_rank=taxon_rank,
                    should_get_children=False,
                    fetch_vernacular_names=False,
                    use_name_lookup=True
                )
                if not taxonomy:
                    # Try again with lookup
                    taxonomy = fetch_all_species_from_gbif(
                        species=species_name,
                        taxonomic_rank=taxon_rank,
                        should_get_children=False,
                        fetch_vernacular_names=False,
                        use_name_lookup=False
                    )
                if not taxonomy:
                    # if there is no record from gbif, create one
                    taxonomy = Taxonomy.objects.create(
                        scientific_name=species_name,
                        canonical_name=species_name,
                        legacy_canonical_name=species_name,
                        rank=taxon_rank
                    )
            else:
                self.add_to_error_summary(
                    'Taxonomy not found {}'.format(species_name),
                    index
                )
                return None
        if taxonomy and self.row_value(record, SPECIES_NAME) not in str(taxonomy.canonical_name):
            taxonomy.legacy_canonical_name = self.row_value(record, SPECIES_NAME)
        # update the taxonomy endemism if different or empty
        if not taxonomy.endemism or taxonomy.endemism != endemism:
            taxonomy.endemism = endemism
            taxonomy.save()
        if self.group:
            self.group.taxonomies.add(taxonomy)
        return taxonomy

    def location_site(self, record):
        location_type, status = LocationType.objects.get_or_create(
            name='PointObservation',
            allowed_geometry='POINT'
        )
        site_description = self.row_value(record, SITE_DESCRIPTION)
        refined_geo = self.row_value(record, REFINED_GEO_ZONE)
        legacy_river_name = self.row_value(record, ORIGINAL_RIVER_NAME)
        record_point = Point(
            float(self.row_value(record, LONGITUDE)),
            float(self.row_value(record, LATITUDE)))
        # Create or get location site
        legacy_site_code = self.row_value(record, ORIGINAL_SITE_CODE)
        try:
            location_site, status = (
                LocationSite.objects.get_or_create(
                    location_type=location_type,
                    geometry_point=record_point,
                    name=self.row_value(record, LOCATION_SITE),
                    legacy_site_code=legacy_site_code
                )
            )
        except LocationSite.MultipleObjectsReturned:
            location_site = LocationSite.objects.filter(
                location_type=location_type,
                geometry_point=record_point,
                name=self.row_value(record, LOCATION_SITE),
                legacy_site_code=legacy_site_code
            )[0]
        if site_description:
            location_site.site_description = site_description
        if refined_geo:
            location_site.refined_geomorphological = refined_geo
        if legacy_river_name:
            location_site.legacy_river_name = legacy_river_name
        location_site.save()
        return location_site

    def biotope(self, record, biotope_record_type, biotope_type):
        biotope = None
        if (
                self.row_value(record, biotope_record_type) and
                self.row_value(record, biotope_record_type).lower() != 'unspecified'):
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

    def handle(self, *args, **options):
        source_collection = options.get('source_collection')
        file_name = options.get('csv_file')
        json_additional_data = options.get('additional_data')
        only_add = options.get('only_add')
        self.find_taxon = ast.literal_eval(
            options.get('find_taxon'))
        if not self.group_key:
            self.group_key = options.get('group_key')
        if self.group_key:
            try:
                self.group = (
                    TaxonGroup.objects.get(name__iexact=self.group_key)
                )
            except TaxonGroup.DoesNotExist:
                self.group = None
        try:
            sites_only = ast.literal_eval(
                options.get('sites_only')
            )
        except ValueError:
            sites_only = False
        try:
            additional_data = json.loads(json_additional_data)
        except ValueError:
            additional_data = {}

        self.disconnect_signals()

        file_path = os.path.join(
            settings.MEDIA_ROOT,
            file_name
        )

        with open(file_path, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for index, record in enumerate(csv_reader):
                try:
                    uuid_value = None

                    # -- Processing LocationSite
                    location_site = self.location_site(record)
                    if sites_only:
                        log('Importing sites data : %s' % str(location_site))
                        continue

                    if UUID in record and self.row_value(record, UUID):
                        try:
                            uuid_value = uuid.UUID(self.row_value(record, UUID)[0:36]).hex
                        except ValueError:
                            self.add_to_error_summary(
                                'Bad UUID format',
                                index
                            )
                            continue
                    if uuid_value:
                        if BiologicalCollectionRecord.objects.filter(
                            uuid=uuid_value
                        ).exists():
                            if only_add:
                                bio = (
                                    BiologicalCollectionRecord.objects.filter(
                                        uuid=uuid_value
                                    )[0]
                                )
                                bio_additional_data = bio.additional_data
                                try:
                                    bio_additional_data = json.loads(
                                        bio_additional_data
                                    )
                                except ValueError:
                                    bio_additional_data = {}
                                for key in additional_data:
                                    bio_additional_data[key] = additional_data[
                                        key]
                                bio.additional_data = bio_additional_data
                                bio.save()
                                continue

                    log('Processing : %s' % self.row_value(record, SPECIES_NAME))
                    optional_records = {}

                    if self.row_value(record, SAMPLING_DATE).lower() == 'unspecified':
                        self.add_to_error_summary(
                            'Unspecified date -> Next row',
                            index
                        )
                        continue
                    sampling_date = self.parse_date(
                        self.row_value(record, SAMPLING_DATE)
                    )

                    # -- Processing Taxonomy
                    taxonomy = self.taxonomy(record, index)
                    if not taxonomy:
                        continue

                    # -- Processing collectors
                    collectors = create_users_from_string(self.row_value(record, COLLECTOR_OR_OWNER))
                    optional_records['collector'] = self.row_value(record, COLLECTOR_OR_OWNER)
                    if len(collectors) > 0:
                        optional_records['collector_user'] = collectors[0]
                        # Add owner and creator to location site
                        # if it doesnt exist yet
                        if not location_site.owner:
                            location_site.owner = collectors[0]
                        if not location_site.creator:
                            location_site.creator = collectors[0]
                        location_site.save()
                        for collector in collectors:
                            collector.organization = self.row_value(record, CUSTODIAN)
                            collector.save()

                    # -- Get superuser as owner
                    superusers = get_user_model().objects.filter(
                        is_superuser=True
                    )

                    # -- Get or create a survey
                    self.survey, _ = Survey.objects.get_or_create(
                        site=location_site,
                        date=sampling_date,
                        collector_user=collectors[0] if len(collectors) > 0 else None,
                        owner=superusers[0]
                    )

                    all_survey_data = {
                        WATER_LEVEL: 'Water level',
                        WATER_TURBIDITY: 'Water turbidity',
                        EMBEDDEDNESS: 'Embeddedness'
                    }
                    for survey_data_key in all_survey_data:
                        if survey_data_key in record and self.row_value(record, survey_data_key):
                            survey_data, _ = SurveyData.objects.get_or_create(
                                name=all_survey_data[survey_data_key]
                            )
                            survey_option = SurveyDataOption.objects.filter(
                                option__iexact=self.row_value(record, survey_data_key).strip(),
                                survey_data=survey_data
                            )
                            if not survey_option.exists():
                                survey_option = SurveyDataOption.objects.create(
                                    options=self.row_value(record, survey_data_key).strip(),
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

                    # -- Processing source reference
                    optional_records['source_reference'] = (
                        self.source_reference(record, index)
                    )

                    # Custodian field)
                    if PRESENT in record:
                        optional_records['present'] = bool(self.row_value(record, PRESENT))
                    category = ''
                    if CATEGORY in record:
                        category = self.row_value(record, CATEGORY).lower()
                    if ORIGIN in record and self.row_value(record, ORIGIN):
                        origin = self.row_value(record, ORIGIN)
                        if (
                                'translocated' in origin.lower() or
                                'non-native' in origin.lower()):
                            category = 'alien'
                        elif 'native' == origin.lower():
                            category = 'native'
                        else:
                            category = None

                    if HABITAT in record and self.row_value(record, HABITAT):
                        habitat_choices = {
                            v: k for k, v in
                            BiologicalCollectionRecord.HABITAT_CHOICES
                        }
                        optional_records['collection_habitat'] = (
                            habitat_choices[self.row_value(record, HABITAT)]
                        )

                    # Sampling method
                    sampling_method = None
                    if SAMPLING_METHOD in record and self.row_value(record, SAMPLING_METHOD):
                        if self.row_value(record, SAMPLING_METHOD).lower() != 'unspecified':
                            try:
                                sampling_method, sm_created = (
                                    SamplingMethod.objects.get_or_create(
                                        sampling_method=self.row_value(record, SAMPLING_METHOD)
                                    )
                                )
                            except SamplingMethod.MultipleObjectsReturned:
                                sampling_method = (
                                    SamplingMethod.objects.filter(
                                        sampling_method=self.row_value(record, SAMPLING_METHOD)
                                    )
                                )[0]

                    # Sampling effort
                    sampling_effort = ''
                    if SAMPLING_EFFORT_VALUE in record and self.row_value(record, SAMPLING_EFFORT_VALUE):
                        sampling_effort += self.row_value(record, SAMPLING_EFFORT_VALUE) + ' '
                    if self.row_value(record, SAMPLING_EFFORT):
                        sampling_effort += self.row_value(record, SAMPLING_EFFORT)
                    optional_records['sampling_effort'] = sampling_effort

                    # -- Processing biotope
                    # Broad biotope
                    optional_records['biotope'] = self.biotope(
                        record,
                        BROAD_BIOTOPE,
                        BIOTOPE_TYPE_BROAD
                    )
                    # Specific biotope
                    optional_records['specific_biotope'] = self.biotope(
                        record,
                        SPECIFIC_BIOTOPE,
                        BIOTOPE_TYPE_SPECIFIC
                    )
                    # Substratum
                    optional_records['substratum'] = self.biotope(
                        record,
                        SUBSTRATUM,
                        BIOTOPE_TYPE_SUBSTRATUM
                    )

                    # -- Processing Abundance
                    abundance_type = ''
                    abundance_number = None

                    if self.row_value(record, ABUNDANCE_MEASURE):
                        abundance_type = self.row_value(record, ABUNDANCE_MEASURE).lower()
                        if 'count' in abundance_type:
                            abundance_type = 'number'
                        elif 'density' in abundance_type:
                            abundance_type = 'density'
                        elif 'percentage' in abundance_type:
                            abundance_type = 'percentage'
                    if self.row_value(record, ABUNDANCE_VALUE):
                        try:
                            abundance_number = float(self.row_value(record, ABUNDANCE_VALUE))
                        except ValueError:
                            pass

                    # -- Processing chemical records
                    self.chemical_records(
                        record,
                        location_site,
                        sampling_date
                    )

                    created = False
                    collection_record = None
                    if uuid_value:
                        collection_records = (
                            BiologicalCollectionRecord.objects.filter(
                                uuid=uuid_value
                            )
                        )
                        if collection_records.exists():
                            collection_records.update(
                                site=location_site,
                                original_species_name=self.row_value(
                                    record,
                                    SPECIES_NAME
                                ),
                                collection_date=sampling_date,
                                taxonomy=taxonomy,
                                category=category,
                                collector=self.row_value(record, COLLECTOR),
                                sampling_method=sampling_method,
                                abundance_type=abundance_type,
                                abundance_number=abundance_number
                            )
                            collection_record = collection_records[0]

                    if not collection_record:
                        fields = {
                            'site': location_site,
                            'original_species_name': self.row_value(record, SPECIES_NAME),
                            'collection_date': sampling_date,
                            'taxonomy': taxonomy,
                            'category': category,
                            'sampling_method': sampling_method,
                            'abundance_type': abundance_type,
                            'abundance_number': abundance_number
                        }
                        if uuid_value:
                            fields['uuid'] = uuid_value
                        try:
                            collection_record, created = (
                                BiologicalCollectionRecord.objects.get_or_create(
                                    **fields
                                )
                            )
                            collection_record.collector = self.row_value(record, COLLECTOR)
                            if not created:
                                if collection_record.uuid and uuid_value:
                                    if collection_record.uuid != uuid_value:
                                        self.data_duplicated += 1
                                        self.add_to_error_summary(
                                            'Duplicated data',
                                            index,
                                            False
                                        )
                                        continue

                        except BiologicalCollectionRecord.MultipleObjectsReturned:
                            BiologicalCollectionRecord.objects.filter(
                                **fields
                            ).delete()
                            collection_record = BiologicalCollectionRecord.objects.create(
                                **fields
                            )
                            created = True

                    # More additional data
                    if CATCH_NUMBER in record:
                        additional_data['catch_per_number'] = (
                            self.row_value(record, CATCH_NUMBER)
                        )
                    if CATCH_PER_UNIT in record:
                        additional_data['catch_per_unit_effort'] = (
                            self.row_value(record, CATCH_PER_UNIT)
                        )
                    if NUMBER_OF_REPLICATES in record:
                        additional_data['number_of_replicates'] = (
                            self.row_value(record, NUMBER_OF_REPLICATES)
                        )

                    collection_record.notes = self.row_value(record, NOTES)
                    collection_record.owner = superusers[0]
                    collection_record.additional_data = additional_data
                    collection_record.source_collection = source_collection
                    collection_record.survey = self.survey
                    if self.group:
                        collection_record.module_group = self.group
                    for field in optional_records:
                        setattr(
                            collection_record, field, optional_records[field])
                    collection_record.save()

                    if not created:
                        self.data_updated += 1
                    else:
                        self.data_added += 1

                    # Update common names
                    if COMMON_NAME in record and self.row_value(record, COMMON_NAME) :
                        common_name = self.row_value(record, COMMON_NAME)
                        try:
                            vernacular_name, vernacular_created = (
                                VernacularName.objects.get_or_create(
                                    name=common_name,
                                    language='eng'
                                )
                            )
                        except VernacularName.MultipleObjectsReturned:
                            vernacular_name = VernacularName.objects.filter(
                                name=common_name
                            )[0]
                        collection_record.taxonomy.vernacular_names.clear()
                        collection_record.taxonomy.vernacular_names.add(
                            vernacular_name)

                    # Import more additional data
                    self.import_additional_data(
                        collection_record,
                        record
                    )

                except KeyError as e:
                    self.add_to_error_summary(
                        'KeyError : {}'.format(e.message), index)
                    continue
                except ValueError as e:
                    self.add_to_error_summary(
                        'ValueError : {}'.format(e.message), index)
                    continue

        self.summary['data_added'] = self.data_added
        self.summary['data_updated'] = self.data_updated
        self.summary['data_failed'] = self.data_failed
        self.summary['data_duplicated'] = self.data_duplicated
        self.summary['total_processed_data'] = (
            self.data_added + self.data_updated + self.data_failed + self.data_duplicated
        )
        self.summary['error_list'] = self.errors
        self.summary['warning_list'] = self.warnings
        log(json.dumps(self.summary))
        self.reconnect_signals()
