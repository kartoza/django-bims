# -*- coding: utf-8 -*-
import sys
import os
import csv
import json
import uuid
from datetime import datetime

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q, signals
from django.utils.text import slugify

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
    SourceReferenceBibliography
)
from td_biblio.models.bibliography import Entry
from td_biblio.utils.loaders import DOILoader, DOILoaderError
from bims.utils.gbif import (
    update_collection_record,
    search_taxon_identifier
)
from geonode.documents.models import Document

SPECIES_NAME = 'Taxon'
TAXON_RANK = 'Taxon rank'
LATITUDE = 'Latitude'
LONGITUDE = 'Longitude'
LOCATION_SITE = 'River'
ORIGINAL_SITE_CODE = 'Original Site Code'
FBIS_SITE_CODE = 'FBIS Site Code'
SITE_DESCRIPTION = 'Site description'
REFINED_GEO_ZONE = 'Refined Geomorphological Zone'
ENDEMISM = 'Endemism'
CATEGORY = 'Category'
ORIGIN = 'Origin'
HABITAT = 'Habitat'
SAMPLING_METHOD = 'Sampling method'
SAMPLING_EFFORT = 'Sampling effort'
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
CONDUCTIVITY = 'Conductivity (mS m-1)'
PH = 'pH'
DISSOLVED_OXYGEN_PERCENT = 'Dissolved Oxygen (%)'
DISSOLVED_OXYGEN_MG = 'Dissolved Oxygen (mg/L)'
TEMP = 'Temperature (deg C)'
TURBIDITY = 'Turbidity (NTU)'

DEPTH_M = 'Depth (m)'
NBV = 'Near Bed Velocity (m/s)'
COLLECTOR_OR_OWNER = 'Collector/Owner'
CUSTODIAN = 'Institute'
NUMBER_OF_REPLICATES = 'Number of replicates'
SAMPLING_DATE = 'Sampling Date'
UUID = 'UUID'
COLLECTOR = 'Collector/Owner'
NOTES = 'Notes'
REFERENCE = 'Reference'
REFERENCE_CATEGORY = 'Reference category'
DOI = 'DOI'
DOCUMENT_UPLOAD_LINK = 'Document Upload Link'
PRESENT = 'Present'
COMMON_NAME = 'Common Name'


class Command(BaseCommand):
    """Import fish data from file"""
    file_name = 'CFR.Fish.csv'

    summary = {}
    data_added = 0
    data_updated = 0
    data_failed = 0
    errors = []

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

    def add_to_error_summary(self, error_message, row):
        error_message = '{id} : {error}'.format(
            id=row,
            error=error_message
        )
        log(error_message)
        self.errors.append(error_message)
        self.data_failed += 1

    def disconnect_signals(self):
        signals.post_save.disconnect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
        signals.post_save.disconnect(
            location_site_post_save_handler,
            sender=LocationSite
        )

    def reconnect_signals(self):
        signals.post_save.connect(
            collection_post_save_handler
        )
        signals.post_save.connect(
            location_site_post_save_handler
        )

    def source_reference(self, record):
        source_reference = None
        reference = record[REFERENCE]
        reference_category = record[REFERENCE_CATEGORY]
        doi = record[DOI].strip()
        document_link = record[DOCUMENT_UPLOAD_LINK]
        document_id = 0
        document = None

        # if there is document link, get the id of the document
        if document_link:
            try:
                doc_split = document_link.split('/')
                document_id = int(doc_split[len(doc_split) - 1])
                document = Document.objects.get(id=document_id)
            except (ValueError, Document.DoesNotExist):
                log('Document {} does not exist'.format(document_id))

        # if DOI provided, check in bibliography records
        if doi:
            try:
                entry = Entry.objects.get(
                    doi=doi
                )
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
                except DOILoaderError:
                    pass
        else:
            if (
                    'peer-reviewed' in reference_category.lower()
            ):
                # Peer reviewed
                # should be bibliography type
                log('Peer reviewed should have a valid doi')
            elif (
                    'published' in reference_category.lower() or
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
                database_record, dr_created = (
                    DatabaseRecord.objects.get_or_create(
                        name=reference
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
                source_reference = (
                    SourceReference.create_source_reference(
                        category=None,
                        source_id=None,
                        note=reference
                    )
                )
        if (
                document and
                source_reference and
                not isinstance(source_reference.source, Document)):
            source_reference.document = document
            source_reference.save()
        return source_reference

    def taxonomy(self, record):
        # if an endemism name exist in the row, check the endemism record
        # from database, if it exists, use that,
        # otherwise create a new one
        endemism = None
        if ENDEMISM in record and record[ENDEMISM]:
            endemism, endemism_created = (
                Endemism.objects.get_or_create(
                    name=record[ENDEMISM]
                )
            )
        # -- Processing taxon species --
        # Find existing taxonomy
        taxa = Taxonomy.objects.filter(
            Q(scientific_name__icontains=record[SPECIES_NAME]) |
            Q(canonical_name__icontains=record[SPECIES_NAME])
        )
        if taxa.exists():
            # if exist, use the first one
            taxonomy = taxa[0]
        else:
            # if not exist, search from gbif
            taxonomy = search_taxon_identifier(record[SPECIES_NAME])
            if not taxonomy:
                # if there is no record from gbif, create one
                taxonomy = Taxonomy.objects.create(
                    scientific_name=record[SPECIES_NAME],
                    canonical_name=record[SPECIES_NAME],
                    rank=record[TAXON_RANK]
                )
        # update the taxonomy endemism if different or empty
        if not taxonomy.endemism or taxonomy.endemism != endemism:
            taxonomy.endemism = endemism
            taxonomy.save()
        return taxonomy

    def location_site(self, record):
        location_type, status = LocationType.objects.get_or_create(
            name='PointObservation',
            allowed_geometry='POINT'
        )
        site_description = record[SITE_DESCRIPTION]
        refined_geo = record[REFINED_GEO_ZONE]
        record_point = Point(
            float(record[LONGITUDE]),
            float(record[LATITUDE]))
        # Create or get location site
        legacy_site_code = record[ORIGINAL_SITE_CODE]
        try:
            location_site, status = (
                LocationSite.objects.get_or_create(
                    location_type=location_type,
                    geometry_point=record_point,
                    name=record[LOCATION_SITE],
                    legacy_site_code=legacy_site_code
                )
            )
        except LocationSite.MultipleObjectsReturned:
            location_site = LocationSite.objects.filter(
                location_type=location_type,
                geometry_point=record_point,
                name=record[LOCATION_SITE],
                legacy_site_code=legacy_site_code
            )[0]
        if site_description:
            location_site.site_description = site_description
        if refined_geo:
            location_site.refined_geomorphological = refined_geo
        location_site.save()
        return location_site

    def biotope(self, record, biotope_record_type, biotope_type):
        biotope = None
        if (
                record[biotope_record_type] and
                record[biotope_record_type].lower() != 'unspecified'):
            biotope, biotope_created = (
                Biotope.objects.get_or_create(
                    biotope_type=biotope_type,
                    name=record[biotope_record_type]
                )
            )
        return biotope

    def collectors(self, record):
        collector_list = []
        collectors = record[COLLECTOR_OR_OWNER]
        User = get_user_model()
        for collector in collectors.split('.,'):
            for collector_name in collector.split('and'):
                collector_name = collector_name.strip()
                if collector_name == '':
                    continue
                if collector_name[len(collector_name)-1] != '.':
                    collector_name += '.'
                collector_name_split = collector_name.split(',')
                if len(collector_name_split) > 1:
                    first_name = collector_name_split[1][0:30]
                    last_name = collector_name_split[0][0:30]
                else:
                    first_name = collector_name_split[0][0:30]
                    last_name = ''
                try:
                    user = User.objects.get(
                        Q(last_name__iexact=last_name),
                        Q(first_name__iexact=first_name) |
                        Q(first_name__istartswith=first_name[0])
                    )
                except User.DoesNotExist:
                    username = slugify('{first_name} {last_name}'.format(
                        first_name= first_name,
                        last_name= last_name
                    )).replace('-', '_')
                    user, created = User.objects.get_or_create(
                        username=username
                    )
                    if created:
                        user.last_name = last_name[0:30]
                        user.first_name = first_name[0:30]
                        user.save()

                collector_list.append(user)
        return collector_list

    def chemical_records(self, record, location_site, date):
        chemical_units = {
            TEMP: 'temperature',
            CONDUCTIVITY: 'conductivity',
            PH: 'ph',
            DISSOLVED_OXYGEN_MG: 'dissolved oxygen',
            DISSOLVED_OXYGEN_PERCENT: (
                'dissolved oxygen: % saturation of '
                'oxygen dissolved in the water'
            ),
            TURBIDITY: 'turbidity (ntu scale)',
            DEPTH_M: 'depth (m)',
            NBV: 'near bed velocity (m/s)'
        }

        for chem_key in chemical_units:
            if not record[chem_key]:
                continue
            chem = Chem.objects.filter(
                chem_description__iexact=chemical_units[chem_key]
            )
            if chem.exists():
                chem = chem[0]
            else:
                chem_unit = chem_key[chem_key.find('(')+1:chem_key.find(')')]
                chem_name = chem_key[0:chem_key.find('(')].strip()
                chem_description = chem_name
                chem = Chem.objects.create(
                    chem_code=chem_name,
                    chem_description=chem_description,
                    chem_unit=chem_unit
                )
            ChemicalRecord.objects.get_or_create(
                date=date,
                chem=chem,
                value=record[chem_key],
                location_site=location_site
            )

    def handle(self, *args, **options):
        source_collection = options.get('source_collection')
        file_name = options.get('csv_file')
        json_additional_data = options.get('additional_data')
        only_add = options.get('only_add')
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
                    if UUID in record and record[UUID]:
                        try:
                            uuid_value = uuid.UUID(record[UUID]).hex
                        except ValueError:
                            pass
                    if uuid_value:
                        if BiologicalCollectionRecord.objects.filter(
                            uuid=uuid_value
                        ).exists():
                            if only_add:
                                continue

                    log('Processing : %s' % record[SPECIES_NAME])
                    optional_records = {}

                    # -- Processing Taxonomy
                    taxonomy = self.taxonomy(record)

                    # -- Processing LocationSite
                    location_site = self.location_site(record)

                    # -- Processing source reference
                    optional_records['source_reference'] = (
                        self.source_reference(record)
                    )

                    # Custodian field
                    if CUSTODIAN in record:
                        optional_records['institution_id'] = (
                            record[CUSTODIAN]
                        )
                    if PRESENT in record:
                        optional_records['present'] = bool(record[PRESENT])
                    category = ''
                    if CATEGORY in record:
                        category = record[CATEGORY].lower()
                    if ORIGIN in record and record[ORIGIN]:
                        origin = record[ORIGIN]
                        if (
                                'translocated' in origin.lower() or
                                'non-native' in origin.lower()):
                            category = 'alien'
                        elif 'native' == origin.lower():
                            category = 'native'
                        else:
                            category = None

                    if HABITAT in record and record[HABITAT]:
                        habitat_choices = {
                            v: k for k, v in
                            BiologicalCollectionRecord.HABITAT_CHOICES
                        }
                        optional_records['collection_habitat'] = (
                            habitat_choices[record[HABITAT]]
                        )

                    # Sampling method
                    sampling_method = None
                    if SAMPLING_METHOD in record and record[SAMPLING_METHOD]:
                        if record[SAMPLING_METHOD].lower() != 'unspecified':
                            try:
                                sampling_method, sm_created = (
                                    SamplingMethod.objects.get_or_create(
                                        sampling_method=record[SAMPLING_METHOD]
                                    )
                                )
                            except SamplingMethod.MultipleObjectsReturned:
                                sampling_method = (
                                    SamplingMethod.objects.filter(
                                        sampling_method=record[SAMPLING_METHOD]
                                    )
                                )[0]
                        optional_records['sampling_method'] = (
                            sampling_method
                        )

                    # Sampling effort
                    sampling_effort = ''
                    if record[SAMPLING_EFFORT_VALUE]:
                        sampling_effort += record[SAMPLING_EFFORT_VALUE]
                    if record[SAMPLING_EFFORT]:
                        sampling_effort += ' ' + record[SAMPLING_EFFORT]
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
                    if record[ABUNDANCE_MEASURE]:
                        optional_records['abundance_type'] = (
                            record[ABUNDANCE_MEASURE]
                        )
                    if record[ABUNDANCE_VALUE]:
                        try:
                            optional_records['abundance_number'] = (
                                float(record[ABUNDANCE_VALUE])
                            )
                        except ValueError:
                            pass

                    if record[SAMPLING_DATE].lower() == 'unspecified':
                        self.add_to_error_summary(
                            'Unspecified date -> Next row',
                            index
                        )
                        continue
                    sampling_date = datetime.strptime(
                        record[SAMPLING_DATE], '%Y/%m/%d')

                    # -- Processing collectors
                    collectors = self.collectors(record)
                    optional_records['collector'] = record[COLLECTOR_OR_OWNER]
                    if len(collectors) > 0:
                        optional_records['collector_user'] = collectors[0]

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
                                original_species_name=record[
                                    SPECIES_NAME
                                ],
                                collection_date=sampling_date,
                                taxonomy=taxonomy,
                                category=category,
                                collector=record[COLLECTOR],
                            )
                            collection_record = collection_records[0]
                        else:
                            optional_records['uuid'] = uuid_value

                    if not collection_record:
                        collection_record, created = (
                            BiologicalCollectionRecord.objects.get_or_create(
                                site=location_site,
                                original_species_name=record[
                                    SPECIES_NAME
                                ],
                                collection_date=sampling_date,
                                taxonomy=taxonomy,
                                category=category,
                                collector=record[COLLECTOR],
                            )
                        )

                    # More additional data
                    if CATCH_NUMBER in record:
                        additional_data['catch_per_number'] = (
                            record[CATCH_NUMBER]
                        )
                    if CATCH_PER_UNIT in record:
                        additional_data['catch_per_unit_effort'] = (
                            record[CATCH_PER_UNIT]
                        )
                    if NUMBER_OF_REPLICATES in record:
                        additional_data['number_of_replicates'] = (
                            record[NUMBER_OF_REPLICATES]
                        )

                    collection_record.notes = record[NOTES]
                    superusers = get_user_model().objects.filter(
                        is_superuser=True
                    )
                    collection_record.owner = superusers[0]
                    collection_record.additional_data = additional_data
                    collection_record.source_collection = source_collection
                    collection_record.save()

                    # update multiple fields
                    BiologicalCollectionRecord.objects.filter(
                        id=collection_record.id
                    ).update(
                        **optional_records
                    )

                    if not created:
                        self.data_updated += 1
                    else:
                        self.data_added += 1

                    # Update common names
                    if COMMON_NAME in record and record[COMMON_NAME]:
                        common_name = record[COMMON_NAME]
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
        self.summary['total_processed_data'] = (
            self.data_added + self.data_updated + self.data_failed
        )
        self.summary['error_list'] = self.errors
        log(json.dumps(self.summary))
        self.reconnect_signals()
