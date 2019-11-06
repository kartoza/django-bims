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

from bims.utils.logger import log
from bims.models import (
    LocationType,
    LocationSite,
    Endemism,
    BiologicalCollectionRecord,
    SamplingMethod,
    VernacularName
)
from bims.utils.gbif import update_collection_record

SPECIES_NAME = 'Taxon'
LATITUDE = 'Latitude'
LONGITUDE = 'Longitude'
LOCATION_SITE = 'River'
ENDEMISM = 'Endemism'
CATEGORY = 'Category'
ORIGIN = 'Origin'
HABITAT = 'Habitat'
SAMPLING_METHOD = 'Sampling method'
EFFORT_AREA = 'Effort (area, m2 )'
EFFORT_TIME = 'Effort (time, min)'
EFFORT_NUMBER_THROWS = 'Effort (number, throws)'
CATCH_NUMBER = 'Catch/number'
CATCH_PER_UNIT = 'Catch Per Unit Effort (CPUE)'
HYDRAULIC_BIOTOPE = 'Hydraulic biotope'
SUBSTRATUM = 'Substratum'
DEPTH_M = 'Depth (m)'
NBV = 'Near Bed Velocity (m/s)'
CONDUCTIVITY = 'Conductivity (mS m-1)'
PH = 'pH'
DISSOLVED_OXYGEN_PERCENT = 'Dissolved Oxygen (%)'
DISSOLVED_OXYGEN_MG = 'Dissolved Oxygen (mg/L)'
TEMP = 'Temperature (°C)'
TURBIDITY = 'Turbidity (NTU)'
CUSTODIAN = 'Institute'
NUMBER_OF_REPLICATES = 'Number of replicates'
SAMPLING_DATE = 'Sampling Date'
UUID = 'uuid'
COLLECTOR = 'Collector/Assessor'
NOTES = 'Notes'
REFERENCE = 'Reference'
REFERENCE_CATEGORY = 'Reference category'
PRESENT = 'Present'
COMMON_NAME = 'Common Name'


class Command(BaseCommand):
    """Import fish data from file"""
    file_name = 'CFR.Fish.csv'

    additional_fields = {
        'present': 'bool',
        'sampling_effort': 'str',
        'reference': 'str',
        'reference_category': 'str',
        'site_description': 'str',
        'site_code': 'str',
        'source_collection': 'str',
    }

    summary = {}
    data_added = 0
    data_updated = 0
    data_failed = 0
    errors = []

    def add_to_error_summary(self, error_message, row):
        error_message = '{id} : {error}'.format(
            id=row,
            error=error_message
        )
        log(error_message)
        self.errors.append(error_message)
        self.data_failed += 1


    def handle(self, *args, **options):
        folder_name = 'data'
        source_collection = 'CFE Fish Data'

        file_path = os.path.join(
            os.path.abspath(os.path.dirname(__name__)),
            'bims/static/{folder}/{filename}'.format(
                folder=folder_name,
                filename=self.file_name
            ))

        with open(file_path, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for index, record in enumerate(csv_reader):
                try:
                    log('Processing : %s' % record[SPECIES_NAME])
                    location_type, status = LocationType.objects.get_or_create(
                        name='PointObservation',
                        allowed_geometry='POINT'
                    )

                    # Optional records for location site
                    optional_site_records = {}

                    # Optional fields and value
                    optional_records = {}

                    if sys.version_info > (3, 0):
                        # Python 3 code in this block
                        optional_fields_iter = self.additional_fields.items()
                    else:
                        # Python 2 code in this block
                        optional_fields_iter = (
                            self.additional_fields.iteritems()
                        )

                    for (opt_field, field_type) in optional_fields_iter:
                        if opt_field in record:
                            optional_record = self.parse_optional_record(
                                record[opt_field],
                                field_type
                            )
                            if not optional_record:
                                optional_record = ''

                            if opt_field[:4] == 'site':
                                optional_site_records[opt_field] = \
                                    optional_record
                            else:
                                if optional_record:
                                    optional_records[opt_field] = \
                                        optional_record

                    record_point = Point(
                        float(record[LONGITUDE]),
                        float(record[LATITUDE]))

                    # Create or get location site
                    try:
                        location_site, status = LocationSite.objects. \
                            get_or_create(
                                location_type=location_type,
                                geometry_point=record_point,
                                name=record[LOCATION_SITE]
                            )
                    except LocationSite.MultipleObjectsReturned:
                        location_site = LocationSite.objects.filter(
                            location_type=location_type,
                            geometry_point=record_point,
                            name=record[LOCATION_SITE]
                        )[0]

                    if sys.version_info > (3, 0):
                        optional_site_records_iter = (
                            optional_site_records.items()
                        )
                    else:
                        optional_site_records_iter = (
                            optional_site_records.iteritems()
                        )

                    for opt_key, opt_val in optional_site_records_iter:
                        setattr(location_site, opt_key, opt_val)
                        location_site.save()

                    # Get existed taxon
                    collections = BiologicalCollectionRecord.objects.filter(
                        original_species_name=record[SPECIES_NAME]
                    )

                    # Endemism
                    endemism = None
                    if ENDEMISM in record and record[ENDEMISM]:
                        endemism, endemism_created = (
                            Endemism.objects.get_or_create(
                                name=record[ENDEMISM]
                            )
                        )

                    taxonomy = None
                    if collections:
                        taxonomy = collections[0].taxonomy

                    if taxonomy:
                        taxonomy.endemism = endemism
                        taxonomy.save()

                    # custodian field
                    if CUSTODIAN in record:
                        optional_records['institution_id'] = \
                            record[CUSTODIAN]

                    # reference
                    if REFERENCE in record:
                        optional_records['reference'] = record[REFERENCE]

                    if REFERENCE_CATEGORY in record:
                        optional_records['reference_category'] = (
                            record[REFERENCE_CATEGORY]
                        )

                    if PRESENT in record:
                        optional_records['present'] = bool(record[PRESENT])

                    category = ''
                    if CATEGORY in record:
                        category = record[CATEGORY].lower()
                    if ORIGIN in record:
                        origin_choices = {
                            v: k for k, v in
                            BiologicalCollectionRecord.CATEGORY_CHOICES
                        }
                        category = origin_choices[record[ORIGIN]]

                    if HABITAT in record:
                        habitat_choices = {
                            v: k for k, v in
                            BiologicalCollectionRecord.HABITAT_CHOICES
                        }
                        optional_records['collection_habitat'] = (
                            habitat_choices[record[HABITAT]]
                        )

                    # sampling method
                    sampling_method = None
                    if SAMPLING_METHOD in record:
                        if record[SAMPLING_METHOD] != 'unspecified':
                            sampling_method, sm_created = (
                                SamplingMethod.objects.get_or_create(
                                    sampling_method=record[SAMPLING_METHOD]
                                )
                            )
                        optional_records['sampling_method'] = (
                            sampling_method
                        )
                    # sampling effort
                    if sampling_method and EFFORT_AREA in record:
                        effort_area = record[EFFORT_AREA]
                        if effort_area:
                            sampling_method.effort_measure = (
                                effort_area + ' m2'
                            )
                            sampling_method.save()
                    if sampling_method and EFFORT_TIME in record:
                        effort_time = record[EFFORT_TIME]
                        if effort_time:
                            sampling_method.effort_measure = (
                                effort_time + ' min'
                            )
                            sampling_method.save()

                    if record[SAMPLING_DATE].lower() == 'unspecified':
                        self.add_to_error_summary(
                            'Unspecified date -> Next row',
                            index
                        )
                        continue

                    created = False
                    collection_records = None
                    if UUID in record and record[UUID]:
                        try:
                            uuid_value = uuid.UUID(record[UUID]).hex
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
                                    collection_date=datetime.strptime(
                                        record[SAMPLING_DATE], '%Y/%m/%d'),
                                    taxonomy=taxonomy,
                                )
                                collection_records = collection_records[0]
                            else:
                                optional_records['uuid'] = uuid_value
                        except ValueError:
                            print('Bad uuid format')

                    if not collection_records:
                        collection_records, created = (
                            BiologicalCollectionRecord.objects.get_or_create(
                                site=location_site,
                                original_species_name=record[
                                    SPECIES_NAME
                                ],
                                collection_date=datetime.strptime(
                                    record[SAMPLING_DATE], '%Y/%m/%d'),
                                taxonomy=taxonomy,
                                category=category,
                                collector=record[COLLECTOR],
                            )
                        )

                    # Additional data
                    additional_data = {}
                    if EFFORT_NUMBER_THROWS in record:
                        additional_data['effort_number_throws'] = (
                            record[EFFORT_NUMBER_THROWS]
                        )
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
                    if HYDRAULIC_BIOTOPE in record:
                        additional_data['hydraulic_biotope'] = (
                            record[HYDRAULIC_BIOTOPE]
                        )
                    if SUBSTRATUM in record:
                        additional_data['substratum'] = (
                            record[SUBSTRATUM]
                        )
                    if DEPTH_M in record:
                        additional_data['depth_m'] = (
                            record[DEPTH_M]
                        )
                    if NBV in record:
                        additional_data['near_bed_velocity'] = (
                            record[NBV]
                        )
                    if CONDUCTIVITY in record:
                        additional_data['conductivity'] = (
                            record[CONDUCTIVITY]
                        )
                    if PH in record:
                        additional_data['ph'] = (
                            record[PH]
                        )
                    if DISSOLVED_OXYGEN_PERCENT in record:
                        additional_data['dissolved_oxygen_percent'] = (
                            record[DISSOLVED_OXYGEN_PERCENT]
                        )
                    if DISSOLVED_OXYGEN_MG in record:
                        additional_data['dissolved_oxygen_mg_l'] = (
                            record[DISSOLVED_OXYGEN_MG]
                        )
                    if TEMP in record:
                        additional_data['temperature'] = (
                            record[TEMP]
                        )
                    if TURBIDITY in record:
                        additional_data['turbidity'] = (
                            record[TURBIDITY]
                        )

                    collection_records.notes = record[NOTES]
                    superusers = get_user_model().objects.filter(
                        is_superuser=True
                    )
                    collection_records.owner = superusers[0]
                    collection_records.additional_data = additional_data
                    collection_records.source_collection = source_collection
                    collection_records.save()

                    # update multiple fields
                    BiologicalCollectionRecord.objects.filter(
                        id=collection_records.id
                    ).update(
                        **optional_records
                    )

                    if not created:
                        self.data_updated += 1
                    else:
                        self.data_added += 1

                    if not taxonomy:
                        log('Update taxon gbif')
                        update_collection_record(collection_records)
                        # If taxonomy still not found
                        if not collection_records.taxonomy:
                            self.add_to_error_summary(
                                'Taxonomy {} not found'.format(
                                    record[SPECIES_NAME]
                                ),
                                index
                            )
                            collection_records.delete()
                            continue
                        collection_records.taxonomy.endemism = endemism
                        collection_records.taxonomy.save()

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
                        collection_records.taxonomy.vernacular_names.clear()
                        collection_records.taxonomy.vernacular_names.add(
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
        self.summary['data_duplicated'] = self.data_updated
        self.summary['data_failed'] = self.data_failed
        self.summary['total_processed_data'] = (
            self.data_added + self.data_updated + self.data_failed
        )
        self.summary['error_list'] = self.errors
        log(json.dumps(self.summary))
